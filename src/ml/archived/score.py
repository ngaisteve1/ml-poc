"""
Azure ML Scoring Script for Archive Forecast Model

This script is used by Azure Machine Learning to serve predictions.
It includes:
1. init() - Load model at deployment time
2. run() - Score incoming requests
3. Feature engineering matching training pipeline

Azure ML requires this exact structure for online endpoints and batch inference.

Usage:
    - Deploy to Azure ML online endpoint
    - Deploy to Azure ML batch inference job
    - Can also be used with Azure Functions
"""

import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model variable
model = None
feature_quantiles = None
model_metadata = None


def init():
    """
    Initialize the model at deployment time.
    This is called once when the endpoint is deployed or when the container starts.
    Load the model from disk and any required artifacts.
    """
    global model, feature_quantiles, model_metadata
    
    try:
        # Get model directory (set by Azure ML)
        model_dir = os.getenv("AZUREML_MODEL_DIR", "./")
        
        # Alternative: Look for model in current directory (for local testing)
        if not os.path.exists(os.path.join(model_dir, "model.joblib")):
            model_dir = Path(__file__).parent.parent.parent / "models"
        
        model_path = Path(model_dir) / "model.joblib"
        quantiles_path = Path(model_dir) / "feature_quantiles.json"
        metadata_path = Path(model_dir) / "model_card.json"
        
        # Load model
        if not model_path.exists():
            logger.error(f"❌ Model not found at {model_path}")
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        model = joblib.load(model_path)
        logger.info(f"✅ Model loaded from: {model_path}")
        
        # Load feature quantiles (for drift detection)
        if quantiles_path.exists():
            with open(quantiles_path, 'r') as f:
                feature_quantiles = json.load(f)
            logger.info(f"✅ Feature quantiles loaded")
        
        # Load model metadata
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                model_metadata = json.load(f)
            logger.info(f"✅ Model metadata loaded: {model_metadata.get('model', 'N/A')}")
        
        logger.info("✅ Model initialization complete")
        
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise RuntimeError(f"Model initialization failed: {e}")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build features from raw input data.
    MUST MATCH the training feature engineering pipeline.
    
    Args:
        df: DataFrame with raw input features
        
    Returns:
        DataFrame with engineered features ready for model prediction
    """
    df_features = df.copy()
    
    try:
        # Expected input columns (from data_preprocessing.py)
        required_cols = [
            'total_files',
            'avg_file_size_mb',
            'pct_pdf',
            'pct_docx',
            'pct_xlsx',
            'archive_frequency_per_day'
        ]
        
        # Check for required columns
        missing_cols = [col for col in required_cols if col not in df_features.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Validate data types and ranges
        df_features['total_files'] = df_features['total_files'].astype(int)
        df_features['avg_file_size_mb'] = df_features['avg_file_size_mb'].astype(float)
        
        # Validate percentage columns sum to <= 1.0
        pct_sum = (df_features['pct_pdf'] + 
                   df_features['pct_docx'] + 
                   df_features['pct_xlsx'])
        
        if (pct_sum > 1.01).any():
            logger.warning("⚠️  File type percentages sum to > 100%, normalizing")
            df_features['pct_pdf'] = df_features['pct_pdf'] / pct_sum
            df_features['pct_docx'] = df_features['pct_docx'] / pct_sum
            df_features['pct_xlsx'] = df_features['pct_xlsx'] / pct_sum
        
        # Calculate other file type percentage
        df_features['pct_other'] = 1.0 - (
            df_features['pct_pdf'] + 
            df_features['pct_docx'] + 
            df_features['pct_xlsx']
        )
        df_features['pct_other'] = df_features['pct_other'].clip(lower=0.0)
        
        # Handle month if provided (for cyclical encoding)
        if 'month' in df_features.columns:
            df_features['month'] = pd.to_datetime(df_features['month'])
            months = df_features['month'].dt.month
        else:
            # Default to current month if not provided
            months = pd.Series([datetime.now().month] * len(df_features))
        
        # Cyclical encoding for seasonality (matches training)
        df_features['month_sin'] = np.sin(2 * np.pi * months / 12)
        df_features['month_cos'] = np.cos(2 * np.pi * months / 12)
        
        # Select final feature columns (MUST match training order)
        feature_cols = [
            'total_files',
            'avg_file_size_mb',
            'pct_pdf',
            'pct_docx',
            'pct_xlsx',
            'pct_other',
            'archive_frequency_per_day',
            'month_sin',
            'month_cos'
        ]
        
        df_final = df_features[feature_cols]
        
        logger.info(f"✅ Features engineered: {df_final.shape[0]} instances × {len(feature_cols)} features")
        
        return df_final
        
    except Exception as e:
        logger.error(f"❌ Feature engineering failed: {e}")
        raise ValueError(f"Feature engineering error: {e}")


def detect_data_drift(df: pd.DataFrame) -> dict:
    """
    Detect potential data drift by comparing with training quantiles.
    
    Returns:
        dict with drift warnings and statistics
    """
    if feature_quantiles is None:
        return {"drift_detected": False, "reason": "No training quantiles available"}
    
    drift_report = {
        "drift_detected": False,
        "anomalies": [],
        "warnings": []
    }
    
    try:
        X = build_features(df)
        
        for col in X.columns:
            if col in feature_quantiles:
                p10 = feature_quantiles[col]['p10']
                p90 = feature_quantiles[col]['p90']
                
                # Check for values outside expected range
                out_of_range = (X[col] < p10) | (X[col] > p90)
                
                if out_of_range.any():
                    drift_report["anomalies"].append({
                        "feature": col,
                        "out_of_range_count": int(out_of_range.sum()),
                        "percentage": float(out_of_range.sum() / len(X) * 100),
                        "expected_p10": p10,
                        "expected_p90": p90,
                        "actual_min": float(X[col].min()),
                        "actual_max": float(X[col].max())
                    })
                    
                    if out_of_range.sum() / len(X) > 0.2:  # >20% out of range
                        drift_report["warnings"].append(
                            f"Significant drift detected in '{col}': {out_of_range.sum()} values "
                            f"({out_of_range.sum() / len(X) * 100:.1f}%) outside training range"
                        )
                        drift_report["drift_detected"] = True
        
    except Exception as e:
        logger.warning(f"⚠️  Could not perform drift detection: {e}")
    
    return drift_report


def run(raw_data):
    """
    Make predictions on incoming data.
    This is called for each prediction request.
    
    Args:
        raw_data: JSON string with prediction instances
        
    Returns:
        JSON string with predictions and metadata
    """
    global model
    
    if model is None:
        error_msg = "Model not initialized. Call init() first."
        logger.error(f"❌ {error_msg}")
        return json.dumps({"error": error_msg, "status": "error"})
    
    try:
        # Parse input
        logger.info(f"Processing prediction request...")
        data = json.loads(raw_data)
        
        # Handle both single instance and batch
        instances = data.get("instances", [data] if "total_files" in data else [])
        
        if not instances:
            raise ValueError("No instances provided in request")
        
        logger.info(f"Scoring {len(instances)} instance(s)")
        
        # Convert to DataFrame
        df = pd.DataFrame(instances)
        
        # Check for data drift
        drift_report = detect_data_drift(df)
        if drift_report["drift_detected"]:
            logger.warning(f"⚠️  Data drift detected: {drift_report['warnings']}")
        
        # Feature engineering
        X = build_features(df)
        
        # Make predictions
        predictions = model.predict(X)
        
        # Format predictions
        results = []
        for i, pred in enumerate(predictions):
            # Handle both single and multi-output models
            if isinstance(pred, (list, np.ndarray)):
                if len(pred) >= 2:
                    results.append({
                        "archived_gb_next_period": float(pred[0]),
                        "savings_gb_next_period": float(pred[1])
                    })
                else:
                    results.append({
                        "archived_gb_next_period": float(pred[0]),
                        "savings_gb_next_period": float(pred[0] * 0.7)  # Fallback estimate
                    })
            else:
                results.append({
                    "archived_gb_next_period": float(pred),
                    "savings_gb_next_period": float(pred * 0.7)
                })
        
        # Build response
        response = {
            "status": "success",
            "predictions": results,
            "instance_count": len(instances),
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_metadata.get("model", "RandomForest") if model_metadata else "Unknown",
            "drift_detected": drift_report["drift_detected"],
            "drift_warnings": drift_report.get("warnings", [])
        }
        
        logger.info(f"✅ Prediction successful: {len(results)} predictions generated")
        
        return json.dumps(response)
    
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON input: {e}"
        logger.error(f"❌ {error_msg}")
        return json.dumps({
            "error": error_msg,
            "status": "error",
            "received_data": str(raw_data)[:100]
        })
    
    except ValueError as e:
        error_msg = f"Data validation error: {e}"
        logger.error(f"❌ {error_msg}")
        return json.dumps({"error": error_msg, "status": "error"})
    
    except Exception as e:
        error_msg = f"Prediction failed: {e}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return json.dumps({
            "error": error_msg,
            "status": "error",
            "error_type": type(e).__name__
        })


# Entry point for local testing
if __name__ == "__main__":
    """
    Test script - run locally to verify score.py works
    
    Usage:
        python src/ml/score.py
        
    Or with custom model path:
        export AZUREML_MODEL_DIR=./models
        python src/ml/score.py
    """
    import os
    
    print("🚀 Testing score.py locally...\n")
    
    # Initialize model
    print("1️⃣  Initializing model...")
    init()
    
    # Create test data
    print("2️⃣  Creating test prediction request...")
    test_request = json.dumps({
        "instances": [
            {
                "month": "2025-01-01",
                "total_files": 120000,
                "avg_file_size_mb": 1.2,
                "pct_pdf": 0.45,
                "pct_docx": 0.30,
                "pct_xlsx": 0.25,
                "archive_frequency_per_day": 320
            },
            {
                "month": "2025-02-01",
                "total_files": 125000,
                "avg_file_size_mb": 1.25,
                "pct_pdf": 0.44,
                "pct_docx": 0.31,
                "pct_xlsx": 0.25,
                "archive_frequency_per_day": 340
            }
        ]
    })
    
    # Make prediction
    print("3️⃣  Making predictions...")
    result = run(test_request)
    
    # Display results
    print("4️⃣  Results:\n")
    result_json = json.loads(result)
    print(json.dumps(result_json, indent=2))
    
    print("\n✅ Test complete!")

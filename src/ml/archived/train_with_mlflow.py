"""
MLflow Integration for ML POC - Training with Experiment Tracking

This script trains the ML model while automatically logging to MLflow:
- Metrics (MAE, R², etc.)
- Parameters (model hyperparameters)
- Artifacts (model file, feature importance)
- Plots and visualizations

The script creates experiments and runs that you can view at:
http://127.0.0.1:5000/

Usage:
    python src/ml/train_with_mlflow.py
    python src/ml/train_with_mlflow.py --data-path data/training_data.csv
    python src/ml/train_with_mlflow.py --out-dir models --experiment-name "archive-forecast-v2"
"""

import argparse
import os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import mlflow
import mlflow.sklearn
import joblib
import json
from datetime import datetime

# MLflow configuration
MLFLOW_URI = "http://127.0.0.1:5000"
EXPERIMENT_NAME = "Archive-Forecast-ML-POC"
RANDOM_STATE = 42


def setup_mlflow(experiment_name: str = EXPERIMENT_NAME):
    """Set up MLflow tracking."""
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(experiment_name)
    print(f"✅ MLflow configured: {MLFLOW_URI}")
    print(f"📊 Experiment: {experiment_name}")


def load_data(data_path: str = "data/training_data.csv") -> pd.DataFrame:
    """Load training data from CSV."""
    df = pd.read_csv(data_path)
    print(f"✅ Loaded data: {data_path}")
    print(f"📊 Shape: {df.shape}")
    return df


def prepare_features(df: pd.DataFrame):
    """Prepare features and targets."""
    # Feature columns
    feature_cols = [
        'files_archived',
        'avg_file_size_mb',
        'largest_file_mb',
        'pct_pdf',
        'pct_docx',
        'pct_xlsx',
        'archive_frequency_per_day',
        'deleted_files_count',
        'tenant_count',
        'site_count'
    ]
    
    # Target columns
    target_cols = ['volume_gb', 'storage_saved_gb']
    
    X = df[feature_cols]
    y = df[target_cols]
    
    print(f"✅ Features: {len(feature_cols)} columns")
    print(f"✅ Targets: {len(target_cols)} columns")
    
    return X, y, feature_cols, target_cols


def create_pipeline():
    """Create preprocessing and model pipeline."""
    # Preprocessing: Scale features
    preprocessor = ColumnTransformer(
        transformers=[
            ('scaler', StandardScaler(), slice(None))
        ]
    )
    
    # Model: Multi-output Random Forest
    model = MultiOutputRegressor(
        RandomForestRegressor(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
    )
    
    # Pipeline
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model)
    ])
    
    return pipeline


def train_model(X_train, X_test, y_train, y_test, pipeline):
    """Train model and return predictions."""
    print("\n🔄 Training model...")
    pipeline.fit(X_train, y_train)
    
    # Predictions
    y_train_pred = pipeline.predict(X_train)
    y_test_pred = pipeline.predict(X_test)
    
    print("✅ Model training complete")
    
    return y_train_pred, y_test_pred


def calculate_metrics(y_train, y_train_pred, y_test, y_test_pred):
    """Calculate evaluation metrics."""
    metrics = {}
    
    # Training metrics
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    train_r2 = r2_score(y_train, y_train_pred)
    
    # Test metrics
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_r2 = r2_score(y_test, y_test_pred)
    
    metrics['train_mae'] = train_mae
    metrics['train_rmse'] = train_rmse
    metrics['train_r2'] = train_r2
    metrics['test_mae'] = test_mae
    metrics['test_rmse'] = test_rmse
    metrics['test_r2'] = test_r2
    
    print("\n📊 Metrics:")
    print(f"   Train MAE: {train_mae:.4f} | Train RMSE: {train_rmse:.4f} | Train R²: {train_r2:.4f}")
    print(f"   Test MAE:  {test_mae:.4f} | Test RMSE:  {test_rmse:.4f} | Test R²:  {test_r2:.4f}")
    
    return metrics


def log_to_mlflow(pipeline, metrics, feature_cols, target_cols, X_train, X_test, y_train, y_test):
    """Log model, metrics, and artifacts to MLflow."""
    
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        print(f"\n📝 MLflow Run ID: {run_id}")
        
        # Log parameters
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 20)
        mlflow.log_param("min_samples_split", 5)
        mlflow.log_param("min_samples_leaf", 2)
        mlflow.log_param("test_size", 0.2)
        mlflow.log_param("random_state", RANDOM_STATE)
        
        # Log metrics
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)
        
        # Log model
        mlflow.sklearn.log_model(pipeline, "model")
        
        # Log feature importance
        feature_importance = pipeline.named_steps['model'].estimators_[0].feature_importances_
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)
        
        # Save and log feature importance plot
        import matplotlib.pyplot as plt
        import tempfile
        plt.figure(figsize=(10, 6))
        plt.barh(importance_df['feature'], importance_df['importance'])
        plt.xlabel('Importance')
        plt.title('Feature Importance')
        plt.tight_layout()
        
        # Use temp directory that works on Windows
        temp_file = Path(tempfile.gettempdir()) / 'feature_importance.png'
        plt.savefig(temp_file, dpi=100)
        mlflow.log_artifact(str(temp_file))
        plt.close()
        
        # Log feature importance data
        mlflow.log_table(importance_df, "feature_importance.json")
        
        # Log tags
        mlflow.set_tag("model_type", "MultiOutputRandomForest")
        mlflow.set_tag("data_type", "archive_metrics")
        mlflow.set_tag("targets", ",".join(target_cols))
        
        print("✅ Model, metrics, and artifacts logged to MLflow")
        
        return run_id


def save_model_locally(pipeline, out_dir: str = "models"):
    """Save model locally as backup."""
    out_path = Path(out_dir)
    out_path.mkdir(exist_ok=True)
    
    model_path = out_path / "model.joblib"
    joblib.dump(pipeline, model_path)
    print(f"✅ Model saved: {model_path}")
    
    return model_path


def main():
    parser = argparse.ArgumentParser(
        description="Train ML model with MLflow tracking"
    )
    parser.add_argument(
        "--data-path",
        default="data/training_data.csv",
        help="Path to training data CSV (default: data/training_data.csv)"
    )
    parser.add_argument(
        "--out-dir",
        default="models",
        help="Output directory for model (default: models)"
    )
    parser.add_argument(
        "--experiment-name",
        default=EXPERIMENT_NAME,
        help=f"MLflow experiment name (default: {EXPERIMENT_NAME})"
    )
    parser.add_argument(
        "--mlflow-uri",
        default=MLFLOW_URI,
        help=f"MLflow tracking URI (default: {MLFLOW_URI})"
    )
    
    args = parser.parse_args()
    
    try:
        # Setup
        print("🚀 Starting ML training with MLflow tracking...\n")
        setup_mlflow(args.experiment_name)
        
        # Load and prepare data
        df = load_data(args.data_path)
        X, y, feature_cols, target_cols = prepare_features(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=RANDOM_STATE
        )
        print(f"✅ Data split: {len(X_train)} train, {len(X_test)} test")
        
        # Create and train model
        pipeline = create_pipeline()
        y_train_pred, y_test_pred = train_model(X_train, X_test, y_train, y_test, pipeline)
        
        # Calculate metrics
        metrics = calculate_metrics(y_train, y_train_pred, y_test, y_test_pred)
        
        # Log to MLflow
        run_id = log_to_mlflow(pipeline, metrics, feature_cols, target_cols, 
                               X_train, X_test, y_train, y_test)
        
        # Save locally
        model_path = save_model_locally(pipeline, args.out_dir)
        
        print(f"\n✅ Training complete!")
        print(f"\n📊 View results at: {args.mlflow_uri}")
        print(f"📈 Experiment: {args.experiment_name}")
        print(f"🏷️  Run ID: {run_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()

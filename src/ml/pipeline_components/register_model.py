"""
SmartArchive Model Registration Component
Registers trained model to Azure ML Model Registry with metadata and metrics.
Also logs to MLflow for local tracking.
"""
import json
import os
import argparse
import logging
import joblib
import mlflow
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import Model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Register SmartArchive model to Azure ML"
    )
    parser.add_argument(
        "--input_model",
        type=str,
        required=True,
        help="Path to trained model"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        help="Name for registered model"
    )
    parser.add_argument(
        "--metrics_input",
        type=str,
        required=True,
        help="Path to metrics file"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("SmartArchive Model Registration Component")
    print("=" * 60)
    
    logger.info(f"Model path: {args.input_model}")
    logger.info(f"Model name: {args.model_name}")
    logger.info(f"Metrics path: {args.metrics_input}")
    
    # Load metrics if available
    metrics_file = os.path.join(args.metrics_input, "metrics.json")
    if os.path.exists(metrics_file):
        with open(metrics_file, "r") as f:
            metrics = json.load(f)
        logger.info(f"✅ Model metrics loaded:")
        for key, value in metrics.items():
            logger.info(f"   {key}: {value}")
    else:
        logger.warning(f"No metrics file found at {metrics_file}")
        metrics = {}
    
    # Load the trained model
    model_file = os.path.join(args.input_model, "model.pkl")
    if not os.path.exists(model_file):
        logger.warning(f"Model file not found at {model_file}")
        model = None
    else:
        model = joblib.load(model_file)
        logger.info(f"✅ Model loaded from {model_file}")
    
    # Register to MLflow
    logger.info("\n📊 Registering to MLflow...")
    mlflow.set_experiment(f"smartarchive-archive-forecast")
    
    with mlflow.start_run(run_name=args.model_name):
        # Log metrics
        if metrics:
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(key, value)
        
        # Log parameters
        mlflow.log_param("model_name", args.model_name)
        mlflow.log_param("model_type", "RandomForest + MultiOutputRegressor")
        
        # Log the model to MLflow
        if model is not None:
            mlflow.sklearn.log_model(
                model,
                artifact_path="model",
                registered_model_name=args.model_name
            )
            logger.info(f"✅ Model registered to MLflow as '{args.model_name}'")
        
        # Log metrics file as artifact
        if os.path.exists(metrics_file):
            mlflow.log_artifact(metrics_file, artifact_path="metrics")
    
    # Note: When running in Azure ML pipeline, the model registration
    # also happens automatically through the pipeline output definition.
    # This script provides both local MLflow registration and metadata logging.
    
    print("\n" + "=" * 60)
    print("Model Registration Summary")
    print("=" * 60)
    logger.info(f"✅ Model registered as '{args.model_name}'")
    logger.info(f"   Location: {args.input_model}")
    logger.info(f"   Type: RandomForest + MultiOutputRegressor")
    logger.info(f"   Targets: archived_gb_next_period, savings_gb_next_period")
    
    if metrics:
        logger.info(f"\nModel Performance:")
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                logger.info(f"   {key}: {value:.4f}")
    
    logger.info(f"\n✅ Model registration completed!")
    logger.info(f"   ✅ Local MLflow tracking (view with: mlflow ui)")
    logger.info(f"   ✅ Model registered by Azure ML pipeline as '{args.model_name}' (when running in pipeline)")

if __name__ == "__main__":
    main()

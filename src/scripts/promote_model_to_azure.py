"""
Promote MLflow Model to Azure ML Model Registry
Registers a model from local MLflow to Azure ML Studio
"""
import json
import os
import argparse
import logging
import subprocess
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model
from azure.identity import AzureCliCredential, DefaultAzureCredential
import mlflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Promote MLflow model to Azure ML Studio"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        help="Name of model in MLflow to promote"
    )
    parser.add_argument(
        "--model_version",
        type=str,
        default="1",
        help="Version of model in MLflow (default: 1)"
    )
    parser.add_argument(
        "--azure_model_name",
        type=str,
        required=True,
        help="Name for model in Azure ML (can be same as model_name)"
    )
    args = parser.parse_args()
    
    print("=" * 80)
    print("MLflow → Azure ML Model Promotion")
    print("=" * 80)
    
    # --- Load Azure configuration ---
    config_path = "azure_config.json"
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"{config_path} not found.\n"
            "Please create it with your Azure subscription, resource group, and workspace."
        )
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    subscription_id = config["subscription_id"]
    resource_group = config["resource_group"]
    workspace_name = config["workspace_name"]
    
    print(f"\n📋 Configuration:")
    print(f"  Subscription: {subscription_id}")
    print(f"  Resource Group: {resource_group}")
    print(f"  Workspace: {workspace_name}")
    print(f"\n🔄 Model Details:")
    print(f"  MLflow Model: {args.model_name} (v{args.model_version})")
    print(f"  Azure ML Name: {args.azure_model_name}")
    
    # --- Connect to Azure ML ---
    print(f"\n🔗 Connecting to Azure ML workspace...")
    
    # Check if Azure CLI is available
    try:
        result = subprocess.run(["az", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            raise FileNotFoundError("Azure CLI not found")
        print(f"✅ Azure CLI found")
    except FileNotFoundError:
        print("\n⚠️  Warning: Azure CLI path check failed in conda environment")
        print("   But we'll try to connect anyway using stored credentials...")
        print("   If this fails, run 'az login' in regular PowerShell first\n")
    
    try:
        # Use AzureCliCredential specifically
        credential = AzureCliCredential()
        ml_client = MLClient(
            credential=credential,
            subscription_id=subscription_id,
            resource_group_name=resource_group,
            workspace_name=workspace_name
        )
        print(f"✅ Connected to Azure ML workspace: {workspace_name}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Azure ML: {e}")
        print("\n📋 Troubleshooting:")
        print("   1. Make sure you've run 'az login' in regular PowerShell")
        print("   2. Check your Azure credentials are valid")
        print("   3. Verify subscription/resource group/workspace in azure_config.json")
        print("   4. Try again")
        raise
    
    # --- Get MLflow model ---
    print(f"\n🔍 Retrieving MLflow model...")
    try:
        mlflow.set_tracking_uri("file:./mlruns")
        client = mlflow.tracking.MlflowClient()
        
        # Get model version details
        model_version = client.get_model_version(args.model_name, args.model_version)
        run_id = model_version.run_id
        model_uri = model_version.source
        
        print(f"✅ MLflow Model Found:")
        print(f"   Name: {args.model_name}")
        print(f"   Version: {args.model_version}")
        print(f"   Run ID: {run_id}")
        print(f"   URI: {model_uri}")
        
        # Convert MLflow URI to actual file path
        # MLflow URI is like: models:/m-xxxxx
        # We need to find the actual model directory in mlruns
        if model_uri.startswith("models:/"):
            # Extract the model hash from the URI
            model_hash = model_uri.replace("models:/", "")
            # Look in mlruns for the model directory
            mlruns_path = os.path.join("mlruns", run_id, "artifacts")
            if os.path.exists(mlruns_path):
                model_path = os.path.join(mlruns_path, "model")
                if os.path.exists(model_path):
                    print(f"   Local Path: {os.path.abspath(model_path)}")
                else:
                    # Try to find model directory
                    for root, dirs, files in os.walk(mlruns_path):
                        if "model.pkl" in files or "MLmodel" in files:
                            model_path = root
                            print(f"   Local Path: {os.path.abspath(model_path)}")
                            break
        else:
            model_path = model_uri
        
    except Exception as e:
        logger.error(f"❌ Failed to find MLflow model: {e}")
        print(f"\nAvailable models: {[m.name for m in client.search_registered_models()]}")
        raise
    
    # --- Register model in Azure ML ---
    print(f"\n📤 Registering model in Azure ML Studio...")
    try:
        # Build the correct path to the model artifacts
        # MLflow stores registered models in: mlruns/{experiment_id}/models/{model_hash}/artifacts
        mlruns_root = "mlruns"
        
        # Find the model directory
        model_path = None
        for exp_dir in os.listdir(mlruns_root):
            models_dir = os.path.join(mlruns_root, exp_dir, "models")
            if os.path.isdir(models_dir):
                for model_dir in os.listdir(models_dir):
                    model_candidate = os.path.join(models_dir, model_dir, "artifacts")
                    if os.path.isdir(model_candidate) and os.path.exists(os.path.join(model_candidate, "MLmodel")):
                        # Found it!
                        model_path = model_candidate
                        print(f"✅ Found model at: {os.path.abspath(model_path)}")
                        break
                if model_path:
                    break
        
        if not model_path:
            raise FileNotFoundError("Could not find MLflow model artifacts directory with MLmodel file")
        
        # Register model in Azure ML
        model = Model(
            path=model_path,
            name=args.azure_model_name,
            description=f"Promoted from MLflow: {args.model_name}",
            type="mlflow_model"
        )
        
        registered_model = ml_client.models.create_or_update(model)
        
        print(f"✅ Model registered in Azure ML:")
        print(f"   Name: {registered_model.name}")
        print(f"   Version: {registered_model.version}")
        print(f"   ID: {registered_model.id}")
    except Exception as e:
        logger.error(f"❌ Failed to register model in Azure ML: {e}")
        raise
    
    # --- Summary ---
    print("\n" + "=" * 80)
    print("✅ Model Promotion Complete!")
    print("=" * 80)
    print(f"\n🎉 Your model is now in Azure ML Studio!")
    print(f"\n📍 View in Azure Portal:")
    print(f"   https://ml.azure.com/models/{args.azure_model_name}/versions/{registered_model.version}")
    print(f"\n📊 Next Steps:")
    print(f"   1. Go to Azure ML Studio")
    print(f"   2. Models → {args.azure_model_name}")
    print(f"   3. Deploy as endpoint or use in pipelines")
    print("=" * 80)

if __name__ == "__main__":
    main()

"""
Register trained model in Azure Machine Learning Model Registry

This script takes a trained model and registers it in Azure ML workspace.
Enables:
- Model versioning and history
- Model promotion (Dev → Staging → Production)
- A/B testing with multiple model versions
- Auto-deployment triggers
- Compliance and governance tracking

Usage:
    python src/ml/register_model.py \\
        --model-path models/model.joblib \\
        --model-name archive-forecast \\
        --version 1.0.0 \\
        --tags env=production,owner=ml-team

Reference:
    https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime
import logging

# Azure ML imports
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_ml_client(subscription_id: str = None, resource_group: str = None, workspace_name: str = None):
    """
    Create Azure ML client for authentication and workspace access.
    
    Args:
        subscription_id: Azure subscription ID (uses env var if not provided)
        resource_group: Azure resource group (uses env var if not provided)
        workspace_name: Azure ML workspace name (uses env var if not provided)
    
    Returns:
        MLClient configured for workspace
    """
    
    # Get values from environment or parameters
    subscription_id = subscription_id or os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_group = resource_group or os.getenv("AZURE_RESOURCE_GROUP", "ml-poc-rg")
    workspace_name = workspace_name or os.getenv("AZURE_ML_WORKSPACE", "ml-poc-ws")
    
    if not subscription_id:
        raise ValueError(
            "subscription_id required. Set AZURE_SUBSCRIPTION_ID env var or pass --subscription-id"
        )
    
    logger.info(f"Connecting to Azure ML...")
    logger.info(f"  Subscription: {subscription_id}")
    logger.info(f"  Resource Group: {resource_group}")
    logger.info(f"  Workspace: {workspace_name}")
    
    try:
        # Try interactive browser auth first (for development)
        credential = InteractiveBrowserCredential()
    except Exception:
        # Fallback to default credential (for CI/CD)
        credential = DefaultAzureCredential()
    
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name
    )
    
    logger.info("✅ Connected to Azure ML workspace")
    return ml_client


def register_model(
    ml_client,
    model_path: str,
    model_name: str,
    version: str,
    description: str = None,
    tags: dict = None,
    properties: dict = None
):
    """
    Register model in Azure ML Model Registry.
    
    Args:
        ml_client: Azure ML client
        model_path: Path to trained model file
        model_name: Name for model in registry
        version: Version string (e.g., "1.0.0")
        description: Model description
        tags: Dictionary of tags (e.g., {"env": "production"})
        properties: Dictionary of properties (e.g., {"accuracy": 0.95})
    
    Returns:
        Registered model object
    """
    
    model_path = Path(model_path)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    logger.info(f"\n📦 Registering model...")
    logger.info(f"  Model file: {model_path}")
    logger.info(f"  Size: {model_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Prepare model metadata
    description = description or f"Archive forecast model trained on {datetime.now().strftime('%Y-%m-%d')}"
    
    tags = tags or {}
    tags.update({
        "training_date": datetime.now().isoformat(),
        "model_type": "RandomForestRegressor",
        "task": "archive_volume_prediction"
    })
    
    properties = properties or {}
    properties.update({
        "model_framework": "scikit-learn",
        "feature_count": 9,
        "target_count": 2
    })
    
    logger.info(f"  Name: {model_name}")
    logger.info(f"  Version: {version}")
    logger.info(f"  Tags: {tags}")
    logger.info(f"  Properties: {properties}")
    
    # Create Model entity
    model = Model(
        path=str(model_path),
        name=model_name,
        version=version,
        description=description,
        tags=tags,
        properties=properties,
        type="custom_model"  # or "mlflow_model" if using MLflow format
    )
    
    # Register model
    logger.info("\n🔄 Registering with Azure ML...")
    registered_model = ml_client.models.create_or_update(model)
    
    logger.info(f"✅ Model registered successfully!")
    logger.info(f"  Model ID: {registered_model.id}")
    logger.info(f"  Name: {registered_model.name}")
    logger.info(f"  Version: {registered_model.version}")
    
    return registered_model


def get_model_info(ml_client, model_name: str, version: str = None):
    """
    Get information about a registered model.
    
    Args:
        ml_client: Azure ML client
        model_name: Model name
        version: Model version (if None, gets latest)
    
    Returns:
        Model information
    """
    
    try:
        if version:
            logger.info(f"\n📋 Fetching model: {model_name} v{version}")
            model = ml_client.models.get(name=model_name, version=version)
        else:
            logger.info(f"\n📋 Fetching latest version of: {model_name}")
            model = ml_client.models.get(name=model_name)
        
        logger.info(f"✅ Model found!")
        logger.info(f"  ID: {model.id}")
        logger.info(f"  Name: {model.name}")
        logger.info(f"  Version: {model.version}")
        logger.info(f"  Path: {model.path}")
        logger.info(f"  Description: {model.description}")
        
        if model.tags:
            logger.info(f"  Tags:")
            for key, value in model.tags.items():
                logger.info(f"    - {key}: {value}")
        
        return model
    
    except Exception as e:
        logger.error(f"❌ Could not find model: {e}")
        raise


def list_model_versions(ml_client, model_name: str):
    """
    List all versions of a model.
    
    Args:
        ml_client: Azure ML client
        model_name: Model name
    
    Returns:
        List of model versions
    """
    
    logger.info(f"\n📚 Listing all versions of: {model_name}")
    
    models = ml_client.models.list(name=model_name)
    model_list = list(models)
    
    if not model_list:
        logger.info(f"  No models found with name: {model_name}")
        return []
    
    logger.info(f"✅ Found {len(model_list)} version(s):")
    
    for model in model_list:
        logger.info(f"  - {model.name} v{model.version} ({model.created_on.strftime('%Y-%m-%d %H:%M:%S')})")
    
    return model_list


def delete_model_version(ml_client, model_name: str, version: str):
    """
    Delete a specific model version.
    
    Args:
        ml_client: Azure ML client
        model_name: Model name
        version: Model version
    """
    
    logger.info(f"\n🗑️  Deleting model: {model_name} v{version}")
    
    try:
        ml_client.models.delete(name=model_name, version=version)
        logger.info(f"✅ Model deleted successfully")
    
    except Exception as e:
        logger.error(f"❌ Failed to delete model: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Register ML model in Azure Machine Learning Registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Register model
  python src/ml/register_model.py \\
    --model-path models/model.joblib \\
    --model-name archive-forecast \\
    --version 1.0.0

  # Register with tags and properties
  python src/ml/register_model.py \\
    --model-path models/model.joblib \\
    --model-name archive-forecast \\
    --version 1.1.0 \\
    --tags env=staging,owner=ml-team \\
    --properties accuracy=0.92,rmse=42.5

  # List all versions
  python src/ml/register_model.py \\
    --list archive-forecast

  # Get specific version
  python src/ml/register_model.py \\
    --get archive-forecast \\
    --version 1.0.0
        """
    )
    
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to trained model file (joblib format)"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        help="Name for model in registry"
    )
    parser.add_argument(
        "--version",
        type=str,
        help="Model version (e.g., 1.0.0)"
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Model description"
    )
    parser.add_argument(
        "--tags",
        type=str,
        help="Comma-separated tags (e.g., 'env=prod,owner=team')"
    )
    parser.add_argument(
        "--properties",
        type=str,
        help="Comma-separated properties (e.g., 'accuracy=0.92,rmse=42')"
    )
    parser.add_argument(
        "--subscription-id",
        type=str,
        help="Azure subscription ID (uses AZURE_SUBSCRIPTION_ID env var if not provided)"
    )
    parser.add_argument(
        "--resource-group",
        type=str,
        help="Azure resource group (uses AZURE_RESOURCE_GROUP env var if not provided)"
    )
    parser.add_argument(
        "--workspace-name",
        type=str,
        help="Azure ML workspace name (uses AZURE_ML_WORKSPACE env var if not provided)"
    )
    parser.add_argument(
        "--list",
        type=str,
        metavar="MODEL_NAME",
        help="List all versions of a model"
    )
    parser.add_argument(
        "--get",
        type=str,
        metavar="MODEL_NAME",
        help="Get information about a model"
    )
    parser.add_argument(
        "--delete",
        type=str,
        metavar="MODEL_NAME",
        help="Delete a specific model version"
    )
    
    args = parser.parse_args()
    
    try:
        # Get ML client
        ml_client = get_ml_client(
            subscription_id=args.subscription_id,
            resource_group=args.resource_group,
            workspace_name=args.workspace_name
        )
        
        # Handle different operations
        if args.list:
            list_model_versions(ml_client, args.list)
        
        elif args.get:
            get_model_info(ml_client, args.get, version=args.version)
        
        elif args.delete:
            if not args.version:
                raise ValueError("--version required when using --delete")
            delete_model_version(ml_client, args.delete, args.version)
        
        elif args.model_path and args.model_name and args.version:
            # Register model
            # Parse tags
            tags = {}
            if args.tags:
                for tag in args.tags.split(","):
                    key, value = tag.split("=")
                    tags[key.strip()] = value.strip()
            
            # Parse properties
            properties = {}
            if args.properties:
                for prop in args.properties.split(","):
                    key, value = prop.split("=")
                    try:
                        properties[key.strip()] = float(value.strip())
                    except ValueError:
                        properties[key.strip()] = value.strip()
            
            registered_model = register_model(
                ml_client,
                model_path=args.model_path,
                model_name=args.model_name,
                version=args.version,
                description=args.description,
                tags=tags,
                properties=properties
            )
            
            print(f"\n✅ Model registration complete!")
            print(f"Model ID: {registered_model.id}")
        
        else:
            parser.print_help()
            print("\nError: Provide either --model-path/--model-name/--version, --list, --get, or --delete")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()

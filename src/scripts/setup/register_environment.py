"""
Register environment in Azure ML before deployment
"""
import json
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Environment
from azure.identity import AzureCliCredential

# Load configuration
config_path = "azure_config.json"
with open(config_path, "r") as f:
    config = json.load(f)

subscription_id = config["subscription_id"]
resource_group = config["resource_group"]
workspace_name = config["workspace_name"]

print("=" * 80)
print("Register Environment in Azure ML")
print("=" * 80)

print(f"\n📋 Configuration:")
print(f"  Subscription: {subscription_id}")
print(f"  Resource Group: {resource_group}")
print(f"  Workspace: {workspace_name}")

# Connect to Azure ML
print(f"\n🔗 Connecting to Azure ML workspace...")
try:
    credential = AzureCliCredential()
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name
    )
    print(f"✅ Connected")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    raise

# Create and register environment
print(f"\n📦 Registering environment...")

environment = Environment(
    name="archive-forecast-env",
    version="1",
    description="Environment for SmartArchive archive forecast model scoring",
    conda_file="src/ml/environment.yml",
    image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest"
)

try:
    env_result = ml_client.environments.create_or_update(environment)
    print(f"✅ Environment registered: {env_result.name} (v{env_result.version})")
    print(f"   Description: {env_result.description}")
except Exception as e:
    print(f"⚠️  Environment registration: {e}")
    # May already exist
    try:
        env_result = ml_client.environments.get("archive-forecast-env", version="1")
        print(f"✅ Using existing environment: {env_result.name}")
    except:
        print(f"❌ Failed: {e}")
        raise

print(f"\n" + "=" * 80)
print("✅ Environment Ready!")
print("=" * 80)
print(f"\nNext: Run 'python deploy_endpoint.py' to deploy the model")

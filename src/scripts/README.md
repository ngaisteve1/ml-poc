# Scripts

This folder contains utility scripts for setup, testing, and deployment.

## 📁 Folder Structure

```
scripts/
├── README.md (this file)
├── setup/
│   └── register_environment.py
├── promote_model_to_azure.py
└── test_endpoint_production.py
```

---

## 🚀 Setup Scripts

### `setup/register_environment.py`
Registers a Python environment with the Azure ML workspace.

**Purpose:** Configure and validate Azure ML environment for model training and deployment

**Usage:**
```bash
python scripts/setup/register_environment.py \
  --subscription-id YOUR_SUBSCRIPTION \
  --resource-group YOUR_RESOURCE_GROUP \
  --workspace-name YOUR_WORKSPACE \
  --environment-name ml-poc-env
```

**What it does:**
- Connects to Azure ML workspace
- Registers Python environment
- Installs dependencies
- Validates environment setup

**Prerequisites:**
- Azure CLI installed and authenticated
- Azure subscription access
- Environment variables set (see `config/azure_config.json`)

---

## 📤 Deployment Scripts

### `promote_model_to_azure.py`
Promotes a trained model to Azure ML as an online endpoint.

**Purpose:** Register model and deploy as production endpoint

**Usage:**
```bash
python scripts/promote_model_to_azure.py \
  --model-path models/trained_model.pkl \
  --model-name archive-volume-forecast \
  --version 1.0
```

**What it does:**
- Loads trained model from local path
- Registers model with Azure ML
- Creates online endpoint
- Deploys model for predictions
- Tests endpoint connectivity

**Features:**
- Automatic version management
- Health checks after deployment
- Rollback capability
- Load balancing setup

**Prerequisites:**
- Trained model file available
- Azure ML workspace configured
- Compute resources provisioned

---

## 🧪 Testing Scripts

### `test_endpoint_production.py`
Tests the deployed production endpoint to verify functionality.

**Purpose:** Validate model endpoint is working correctly

**Usage:**
```bash
python scripts/test_endpoint_production.py \
  --endpoint-url https://your-endpoint.inference.ml.azure.com \
  --api-key YOUR_API_KEY
```

**What it does:**
- Connects to deployed endpoint
- Sends test prediction requests
- Validates response format
- Measures latency
- Reports endpoint health

**Output Example:**
```
✓ Endpoint is responding (200 OK)
✓ Response format is valid
✓ Average latency: 245ms
✓ Last 10 requests successful
Status: HEALTHY
```

**Prerequisites:**
- Endpoint deployed and running
- API key for authentication
- Network access to endpoint

---

## 📋 Common Workflows

### Workflow 1: Setup and Register Environment
```bash
# 1. Ensure you're in the right directory
cd ml-poc

# 2. Activate Python environment
conda activate ml-poc-env

# 3. Configure Azure
# Set environment variables from config/azure_config.json

# 4. Register environment
python scripts/setup/register_environment.py
```

### Workflow 2: Train, Promote, and Test
```bash
# 1. Train model (see src/ml/train.py)
python src/ml/train.py --out_dir models

# 2. Promote to Azure
python scripts/promote_model_to_azure.py \
  --model-path models/model.pkl \
  --model-name archive-forecast

# 3. Test the endpoint
python scripts/test_endpoint_production.py \
  --endpoint-url <YOUR_ENDPOINT_URL> \
  --api-key <YOUR_API_KEY>
```

### Workflow 3: Continuous Testing
```bash
# Run tests periodically to monitor endpoint health
while true; do
  python scripts/test_endpoint_production.py
  sleep 300  # Test every 5 minutes
done
```

---

## 🔧 Script Configuration

### Environment Variables
Set these before running scripts:

```bash
# Azure configuration
$env:AZURE_SUBSCRIPTION_ID = "your-subscription-id"
$env:AZURE_RESOURCE_GROUP = "your-resource-group"
$env:AZURE_ML_WORKSPACE = "your-workspace-name"
$env:MLFLOW_TRACKING_URI = "azureml://<workspace-id>"

# Model endpoint
$env:ENDPOINT_URL = "https://your-endpoint.inference.ml.azure.com"
$env:API_KEY = "your-api-key"
```

### Command Line Arguments
Most scripts support command-line arguments:

```bash
# Help for any script
python scripts/setup/register_environment.py --help
python scripts/promote_model_to_azure.py --help
python scripts/test_endpoint_production.py --help
```

---

## 📚 Related Documentation

| Script | Documentation |
|--------|---------------|
| `setup/register_environment.py` | [`docs/guides/AZURE_ML_PIPELINE_GUIDE.md`](../docs/guides/AZURE_ML_PIPELINE_GUIDE.md) |
| `promote_model_to_azure.py` | [`docs/guides/DEPLOYMENT_GUIDE.md`](../docs/guides/DEPLOYMENT_GUIDE.md) |
| `test_endpoint_production.py` | [`docs/guides/COMMAND_REFERENCE.md`](../docs/guides/COMMAND_REFERENCE.md) |

---

## 🐛 Troubleshooting

### "Authentication failed"
```bash
# Re-authenticate with Azure
az logout
az login
```

### "Module not found"
```bash
# Ensure environment is activated and requirements installed
pip install -r config/requirements.txt
```

### "Endpoint connection timeout"
```bash
# Check endpoint is deployed
az ml online-endpoint list

# Check network access
curl https://your-endpoint.inference.ml.azure.com/health
```

---

## 📝 Creating New Scripts

When adding new scripts:

1. **Location**: Place in `scripts/` or `scripts/setup/` as appropriate
2. **Format**: Use Python with `argparse` for CLI arguments
3. **Documentation**: Add docstrings and help text
4. **Error Handling**: Include try-except blocks and user-friendly errors
5. **Logging**: Use Python logging module for debugging

**Template:**
```python
#!/usr/bin/env python3
"""
Script description and purpose.

Usage:
    python scripts/your_script.py --option value
"""

import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(args):
    """Main script logic."""
    logger.info("Starting script...")
    # Your code here
    logger.info("Completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--option", required=True, help="Option description")
    args = parser.parse_args()
    main(args)
```

---

**Last Updated:** November 13, 2025  
**Purpose:** Organized utility scripts for ML POC setup and deployment

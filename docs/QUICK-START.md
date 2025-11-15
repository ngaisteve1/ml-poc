# 🚀 Quick Start: SmartArchive ML-POC Pipeline

**Time:** 15 minutes to first run  
**Difficulty:** Beginner-friendly  
**Status:** ✅ Ready to go

---

## Prerequisites

```bash
# 1. Python 3.10+
python --version

# 2. Azure CLI
az --version

# 3. Git (already have it)
git --version
```

---

## Setup (5 minutes)

### Step 1: Configure Azure

```bash
# Login to Azure
az login

# Select subscription
az account set --subscription "your-subscription-id"

# Verify
az account show
```

### Step 2: Edit Configuration

Open `ml-poc/azure_config.json`:

```bash
# Get your values
az account show --query id              # subscription_id
az group list --query "[].name"         # resource_group
az ml workspace list -g your-rg --query "[].name"  # workspace_name
```

Update the file:
```json
{
  "subscription_id": "your-id-here",
  "resource_group": "your-rg-here",
  "workspace_name": "your-workspace-here"
}
```

### Step 3: Setup Python Environment

```bash
cd ml-poc

# Using Conda
conda env create -f environment.yml
conda activate archive-forecast-prod

# Verify
python -c "import azure.ai.ml; print('✅ Azure ML SDK installed')"
```

---

## Run Locally (First Time)

### Option A: Test Each Component (Recommended for First Run)

```bash
# Terminal 1: Prepare data
python src/ml/pipeline_components/prepare_data.py --output_data ./test_data/prepared

# Terminal 2: Train model  
python src/ml/pipeline_components/train_model.py --input_data ./test_data/prepared --n_estimators 50 --output_model ./test_data/model --metrics_output ./test_data/metrics
```

**Expected Output:**
```
✅ Data loaded. Shape: (1000, 12)
✅ Prepared data saved to ./test_data/prepared/archive-data.csv
...
✅ Model saved to: ./test_data/model
✅ Metrics saved to: ./test_data/metrics/metrics.json
✅ Model registered to MLflow as 'smartarchive-archive-forecast'
```

### Option B: Run Full Pipeline (Automated)

```bash
# From ml-poc directory
python src/ml/azure_ml_pipeline.py
```

**Expected Output:**
```
Connected to Azure ML workspace: mlflow-workspace
✅ Using existing compute cluster: cpu-cluster
✅ Environment registered: smartarchive-pipeline-env
✅ Pipeline submitted successfully!

Pipeline Run ID: abc-123-def
View pipeline at: https://ml.azure.com/...
```

---

## Monitor Execution

### In Azure Portal

1. Go to: [Azure ML Studio](https://ml.azure.com)
2. Select your workspace
3. Go to: **Jobs** → **Pipelines**
4. Click pipeline run ID

### In Terminal

```bash
# Stream logs
az ml job stream --name <pipeline_run_id>

# Check status
az ml job show --name <pipeline_run_id> --query status
```

### View Metrics

```bash
# Start MLflow UI (view locally trained models)
mlflow ui

# Go to: http://localhost:5000
# View experiments, runs, and registered models
```

---

## Promote to Azure ML Studio

Once you have a model registered in MLflow, promote it to Azure ML:

```bash
# Make sure you're logged in to Azure. Make sure install Azure CLI. Set path in window. Restart DOS.
az login

# Promote the model from MLflow to Azure ML Studio
python promote_model_to_azure.py --model_name smartarchive-archive-forecast --model_version 1   --azure_model_name smartarchive-archive-forecast
```

**Expected Output:**
```
✅ Connected to Azure ML workspace: mlflow-workspace
✅ MLflow Model Found
✅ Model registered in Azure ML
🎉 Your model is now in Azure ML Studio!
```

**View in Azure ML Studio:**
- Go to: https://ml.azure.com/models/smartarchive-archive-forecast
- Deploy as endpoint
- Use in production pipelines

---

## Test Azure ML Endpoint

### Setup Environment Variables

```bash
# Create .env file in ml-poc directory
echo "MLFLOW_ENDPOINT=https://your-endpoint.azureml.net/score" > .env
echo "MLFLOW_API_KEY=your-api-key-here" >> .env
```

Get your values from Azure ML Studio:
1. Go to: **Endpoints** → **smartarchive-archive-forecast-1**
2. Copy **REST endpoint URL** → Set as `MLFLOW_ENDPOINT`
3. Copy **Primary key** under Authentication → Set as `MLFLOW_API_KEY`

### Run Endpoint Test

```bash
# Test your deployed Azure ML endpoint
python scripts/test_endpoint_production.py
```

**Expected Output:**
```
========================================================================
AZURE ML ENDPOINT - PRODUCTION TEST
========================================================================

🔗 Endpoint: https://your-endpoint.azureml.net/score
🔑 Deployment: smartarchive-archive-forecast-1

📤 Request Features (9):
   1. total_files: 120000
   2. avg_file_size_mb: 1.2
   ...

📊 Response Status: 200
✅ SUCCESS!

📈 Predictions:
   Forecasted archived_gb_next_period: 1234.56 GB
   Forecasted savings_gb_next_period: 987.65 GB

💾 Model is ready for integration!
```

---

## Troubleshooting

### "authentication failed"
```bash
az logout
az login
# Follow browser prompt
```

### "Module not found"
```bash
pip install --upgrade azure-ai-ml azure-identity mlflow scikit-learn
```

### "Workspace not found"
```bash
# Verify values in azure_config.json
az ml workspace list --resource-group your-rg-name
```

### "Compute cluster error"
```bash
# Check Azure quota
# Portal → Subscription → Usage + Quotas
# May need to request quota increase
```

---

## What's Next?

### ✅ All Working?

1. **Deploy Model:** `DEPLOYMENT_GUIDE.md` (20-30 min)
   - Option 1: REST API (Online Endpoint)
   - Option 2: Batch Inference
   - Option 3: FastAPI Web Service

2. **After Deployment:** `AFTER_DEPLOYMENT_GUIDE.md` (READ THIS NEXT!)
   - Test your endpoint
   - Understanding experiments vs. registered models
   - When to use Pipeline & Data tabs
   - Next steps and monitoring

3. **Monitor in Production:** Set up Application Insights
4. **Automate Retraining:** Create scheduled pipeline
5. **Integrate with SmartArchive:** Connect to backend system

### 📚 Learn More

| Topic | File |
|-------|------|
| Complete setup | `AZURE_ML_PIPELINE_GUIDE.md` |
| Model deployment | `DEPLOYMENT_GUIDE.md` |
| After deployment (READ NEXT!) | `AFTER_DEPLOYMENT_GUIDE.md` |
| Component details | `src/ml/pipeline_components/` |
| Endpoint testing | `scripts/test_endpoint_production.py` |
| Transformation details | `TRANSFORMATION_SUMMARY.md` |

---

## One-Line Quick Test (Local)

```bash
# Test local pipeline in one command
cd ml-poc && python src/ml/pipeline_components/prepare_data.py --output_data ./test && python src/ml/pipeline_components/train_model.py --input_data ./test --output_model ./test/m --metrics_output ./test/mt
```

---

## Success Checklist

- [ ] Python environment created and activated
- [ ] `azure_config.json` configured with your Azure details
- [ ] Data preparation script runs successfully
- [ ] Model training completes
- [ ] Model registered to MLflow (`mlflow ui` shows the model)
- [ ] Model promoted to Azure ML Studio
- [ ] Azure ML endpoint deployed in Azure Studio
- [ ] `.env` file configured with endpoint URL and API key
- [ ] Azure ML endpoint test passes (`scripts/test_endpoint_production.py`)
- [ ] Can view predictions from endpoint

---

## Support

**Issues?** Check `AZURE_ML_PIPELINE_GUIDE.md` → Troubleshooting section

**Questions?** See component docstrings:
```bash
python -c "from src.ml.pipeline_components.train_model import main; help(main)"
```

---

**Ready?** Run: `python src/ml/azure_ml_pipeline.py` 🚀

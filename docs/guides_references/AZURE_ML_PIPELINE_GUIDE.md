# SmartArchive ML-POC: Azure ML Pipeline Integration

**Status:** ✅ Production-Ready ML Pipeline  
**Architecture:** Based on ml-poc-wine working example, adapted for SmartArchive  
**Components:** Data Prep → Model Training → Model Registration

---

## 📁 Structure Overview

```
ml-poc/
├── azure_config.json                    ← Azure ML workspace configuration
├── pipeline_conda.yml                   ← Conda environment specification
├── src/ml/
│   ├── azure_ml_pipeline.py            ← Main pipeline orchestrator
│   ├── pipeline_components/            ← Azure ML Pipeline Components
│   │   ├── prepare_data.py             ← Data preparation & feature engineering
│   │   ├── train_model.py              ← Model training (RandomForest + MultiOutput)
│   │   ├── register_model.py           ← Model registration to Azure ML
│   │   └── __init__.py
│   ├── score.py                        ← Scoring script for Azure ML endpoint
│   ├── main.py                         ← FastAPI REST API
│   └── [other files remain unchanged]
```

---

## 🔧 Setup & Configuration

### 1. Configure Azure Credentials

Edit `azure_config.json` with your Azure subscription details:

```json
{
  "subscription_id": "your-subscription-id",
  "resource_group": "your-resource-group",
  "workspace_name": "your-workspace-name"
}
```

**To get these values:**
```bash
# Get subscription ID
az account show --query id

# List resource groups
az group list --query "[].name"

# List ML workspaces in a resource group
az ml workspace list --resource-group <rg-name> --query "[].name"
```

### 2. Install Azure CLI

```bash
# Windows
winget install Azure.CLI

# Or download from: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows
```

### 3. Authenticate with Azure

```bash
az login
az ml configure --workspace-name your-workspace-name --resource-group your-resource-group
```

### 4. Install Python Dependencies

```bash
cd ml-poc
pip install -r requirements.txt

# Or install specific packages for pipeline
pip install azure-ai-ml azure-identity mlflow scikit-learn pandas numpy
```

---

## 🚀 Running the Pipeline

### Option 1: Submit Pipeline to Azure ML (Recommended)

```bash
cd ml-poc
python src/ml/azure_ml_pipeline.py
```

**What this does:**
1. Connects to your Azure ML workspace
2. Creates/uses compute cluster (STANDARD_DS3_V2)
3. Registers conda environment
4. Defines pipeline components (prepare → train → register)
5. Submits pipeline job to Azure ML
6. Returns pipeline URL to monitor progress

**Expected output:**
```
Connected to Azure ML workspace: mlflow-workspace
✅ Using existing compute cluster: cpu-cluster
✅ Environment registered: smartarchive-pipeline-env
✅ Pipeline submitted successfully!

Pipeline Run ID: abc123def456
Experiment: smartarchive-archive-forecasting
Status: Queued
View pipeline at: https://ml.azure.com/...
```

### Option 2: Run Pipeline Components Locally

Useful for testing before submitting to Azure:

**Step 1: Prepare Data**
```bash
python src/ml/pipeline_components/prepare_data.py \
  --output_data ./local_data/prepared
```

**Step 2: Train Model**
```bash
python src/ml/pipeline_components/train_model.py \
  --input_data ./local_data/prepared \
  --n_estimators 100 \
  --output_model ./local_data/model \
  --metrics_output ./local_data/metrics
```

**Step 3: Register Model**
```bash
python src/ml/pipeline_components/register_model.py \
  --input_model ./local_data/model \
  --model_name smartarchive-archive-forecast \
  --metrics_input ./local_data/metrics
```

---

## 📊 Pipeline Components Explained

### Component 1: Data Preparation (`prepare_data.py`)

**Purpose:** Load and prepare SmartArchive archive data

**Features:**
- Loads from CSV, database, API, or generates synthetic data
- Real SmartArchive schema:
  - `total_files`, `avg_file_size_mb`, `pct_pdf`, `pct_docx`, `pct_xlsx`
  - `archive_frequency_per_day`, `files_archived`
  - `archived_gb`, `savings_gb` (targets)
- Data validation and cleaning
- Feature engineering (percentages normalization)

**Input:**
- Optional: CSV file with SmartArchive data
- Default: Generates synthetic data (1000 records)

**Output:**
- `archive-data.csv` with prepared features and targets

**Command:**
```bash
python prepare_data.py \
  --output_data <output_dir> \
  --input_data <optional_csv>
```

---

### Component 2: Model Training (`train_model.py`)

**Purpose:** Train RandomForest model for archive volume prediction

**Architecture:**
- Model Type: `RandomForestRegressor` + `MultiOutputRegressor`
- Predicts 2 targets:
  1. `archived_gb_next_period` (archive volume)
  2. `savings_gb_next_period` (storage savings)

**Features:**
- Feature engineering (cyclical encoding, normalization)
- Train/test split (80/20)
- StandardScaler normalization
- Hyperparameter control (n_estimators)
- MLflow integration for experiment tracking

**Metrics Calculated:**
```
Per output:
  - MAE (Mean Absolute Error)
  - RMSE (Root Mean Squared Error)
  - R² (Coefficient of Determination)

Average across outputs:
  - Average MAE, RMSE, R²
```

**Input:**
- `prepared_data`: CSV from data preparation step
- `n_estimators`: Number of trees (default 100)

**Output:**
- `trained_model`: MLflow model artifact
- `metrics.json`: Training metrics

**Command:**
```bash
python train_model.py \
  --input_data <prepared_data_dir> \
  --n_estimators 100 \
  --output_model <model_output_dir> \
  --metrics_output <metrics_output_dir>
```

---

### Component 3: Model Registration (`register_model.py`)

**Purpose:** Register model to Azure ML Model Registry

**Features:**
- Loads model and metrics
- Logs metadata to Azure ML
- Prepares for deployment as online endpoint

**In Azure ML Pipeline:**
- Model automatically registered through output definition
- This component logs additional metadata and validation

**Input:**
- `trained_model`: MLflow model from training
- `model_name`: Name for registration (e.g., smartarchive-archive-forecast)
- `metrics`: Metrics from training

**Command:**
```bash
python register_model.py \
  --input_model <model_dir> \
  --model_name smartarchive-archive-forecast \
  --metrics_input <metrics_dir>
```

---

## 📈 Model Details

### Model Architecture
```
Input Features (9):
  ├─ total_files
  ├─ avg_file_size_mb
  ├─ pct_pdf, pct_docx, pct_xlsx, pct_other
  ├─ archive_frequency_per_day
  └─ month_sin, month_cos (cyclical encoding)
        ↓
  RandomForestRegressor (100 trees)
  + MultiOutputRegressor
        ↓
Output Targets (2):
  ├─ archived_gb_next_period
  └─ savings_gb_next_period
```

### Key Parameters
```
RandomForest:
  - n_estimators: 100 (configurable)
  - random_state: 42 (reproducibility)
  - max_depth: 10
  - n_jobs: -1 (use all cores)

Train/Test Split:
  - Test size: 20%
  - Random state: 42

Scaler:
  - StandardScaler (mean 0, std 1)
```

---

## 🔌 Deployment & Scoring

### Deploy Trained Model as REST API

Once model is registered in Azure ML, deploy as online endpoint:

```bash
# Using Azure ML CLI
az ml online-endpoint create -f deployment_config.yaml

# Or using Python SDK (see score.py for details)
```

### Test Predictions

**Via REST API:**
```bash
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [{
      "month": "2024-01-01",
      "total_files": 50000,
      "avg_file_size_mb": 2.5,
      "pct_pdf": 0.4,
      "pct_docx": 0.3,
      "pct_xlsx": 0.2,
      "archive_frequency_per_day": 100.0
    }]
  }'
```

**Expected Response:**
```json
{
  "predictions": [{
    "archived_gb_next_period": 250.45,
    "savings_gb_next_period": 125.22
  }]
}
```

---

## 🔍 Monitoring & MLflow

### View Experiments

```bash
# Start MLflow UI
mlflow ui

# View at: http://localhost:5000
```

### Track Pipeline Runs

```bash
# Get pipeline run details
az ml job show --name <pipeline_run_id>

# Stream logs
az ml job stream --name <pipeline_run_id>

# List all pipeline runs
az ml job list --experiment-name smartarchive-archive-forecasting
```

---

## 🛠️ Troubleshooting

### Issue: "Azure CLI authentication failed"

**Solution:**
```bash
az login
# Follow browser login prompt
az account show
```

### Issue: "Workspace not found"

**Solution:**
```bash
# Verify workspace exists
az ml workspace list --resource-group <rg-name>

# Update azure_config.json with correct values
```

### Issue: "Compute cluster not found or creation failed"

**Solution:**
```bash
# Check available compute
az ml compute list --resource-group <rg-name>

# Increase Azure quota if needed
# Go to: Azure Portal → Subscription → Usage + quotas
```

### Issue: "Module not found" errors

**Solution:**
```bash
pip install --upgrade -r requirements.txt
# Or install specific packages:
pip install azure-ai-ml azure-identity mlflow scikit-learn
```

---

## 📚 Data Source Options

### Option 1: Use Synthetic Data (Default)
```bash
# No input needed, uses generated data
python src/ml/pipeline_components/prepare_data.py --output_data ./data
```

### Option 2: Use Real SmartArchive Data
```bash
# From CSV file
python src/ml/pipeline_components/prepare_data.py \
  --output_data ./data \
  --input_data /path/to/smartarchive_data.csv

# From SQL database (add to prepare_data.py)
# From API endpoint (add to prepare_data.py)
```

### Option 3: Connect to SmartArchive Database

To use real data, modify `prepare_data.py`:

```python
# Add SQL connection (example for SQL Server)
import pyodbc

connection = pyodbc.connect(
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=your-server;'
    'Database=smartarchive_db;'
    'UID=username;'
    'PWD=password'
)

query = """
SELECT 
    month, total_files, avg_file_size_mb, 
    pct_pdf, pct_docx, pct_xlsx,
    archive_frequency_per_day,
    archived_gb, savings_gb
FROM archive_metrics
"""

df = pd.read_sql(query, connection)
```

---

## 🎯 Next Steps

### 1. Test Locally (1 hour)
```bash
python src/ml/pipeline_components/prepare_data.py --output_data ./test_data
python src/ml/pipeline_components/train_model.py --input_data ./test_data ...
```

### 2. Deploy to Azure ML (2 hours)
```bash
python src/ml/azure_ml_pipeline.py
# Monitor at Azure Portal ML Studio
```

### 3. Connect Real Data (varies)
- Extract from SmartArchive database
- Update `prepare_data.py` with connection logic
- Retrain with production data

### 4. Deploy Model as Endpoint (1 hour)
```bash
az ml online-endpoint create -f deployment_config.yaml
```

### 5. Monitor Production (ongoing)
- Set up drift detection (monitor.py)
- Configure alerts for performance degradation
- Schedule retraining pipeline (weekly/monthly)

---

## 📖 Additional Resources

- **Azure ML Documentation:** https://learn.microsoft.com/en-us/azure/machine-learning/
- **MLflow Documentation:** https://mlflow.org/docs/latest/
- **Pipeline Components:** See `pipeline_components/` folder
- **Deployment Guide:** See `deployment_config.yaml`
- **Scoring Guide:** See `score.py`

---

## ✅ Validation Checklist

- [ ] `azure_config.json` configured with Azure details
- [ ] Azure CLI installed and authenticated (`az login`)
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Pipeline components tested locally
- [ ] Azure ML workspace accessible
- [ ] Compute cluster available or auto-creation enabled
- [ ] Pipeline submitted successfully to Azure ML
- [ ] Model registered and visible in Azure ML Studio
- [ ] Model deployed as online endpoint
- [ ] REST API predictions working

---

**Document:** SmartArchive ML-POC Pipeline Integration Guide  
**Version:** 1.0  
**Date:** November 3, 2025  
**Status:** ✅ Production Ready

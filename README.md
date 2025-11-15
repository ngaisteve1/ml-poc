# ML POC: Archive Volume & Storage Savings Forecast

This Python project trains a regression model on historical archive data (file sizes, types, archive frequency) to predict:
- Archive volume for the next month/quarter
- Storage space expected to be saved

It exposes a FastAPI web API for predictions and logs experiments with MLflow. Optional Azure ML integration is available.

## 📁 Project Structure

```
ml-poc/
├── docs/                          Documentation & reference materials
│   ├── getting-started/           Quick start guides
│   ├── guides/                    Detailed how-to guides
│   ├── references/                Reference documentation
│   ├── sql/                       SQL setup scripts
│   └── archived/                  Outdated documentation
├── src/                           Source code
│   ├── ml/                        ML pipeline components
│   │   ├── pipeline_components/   Data prep, training, registration
│   │   ├── archived/              Experimental/old code
│   │   └── azure_ml_pipeline.py   Azure ML orchestration
│   ├── app/                       FastAPI application
│   └── tests/                     Unit tests
├── test_data/                     Test data & models
│   ├── model/                     Trained model artifacts
│   ├── prepared/                  Preprocessed test data
│   ├── archive-data.csv           Sample archive data
│   └── training_data.csv          Model training data
├── config/                        Configuration files
│   ├── azure_config.json          Azure settings
│   ├── environment.yml            Conda environment
│   ├── pyproject.toml             Python project config
│   └── requirements.txt           Python dependencies
├── scripts/                       Utility scripts
│   ├── setup/                     Environment setup
│   ├── promote_model_to_azure.py  Model deployment
│   └── test_endpoint_production.py Endpoint testing
└── [Config files, README, etc.]
```

## 📊 Data Extraction & Preprocessing

**Complete SQL queries and Python utilities** for extracting data from SmartArchive database.

See these resources:
- **`docs/sql/`**: SQL setup and extraction queries
- **`docs/guides/`**: Data extraction and preprocessing guides
- **`src/ml/pipeline_components/prepare_data.py`**: Data loading, validation, and feature engineering

### Quick Extract & Process

```python
# 1. Extract data from database using SQL in docs/sql/
# 2. Load and preprocess using pipeline components
from src.ml.pipeline_components.prepare_data import load_and_prepare_data

# Load and prepare data
X_train, X_test, y_train, y_test, scaler = load_and_prepare_data(
    data_path='test_data/training_data.csv',
    test_size=0.2
)

# Data is now ready for training
```

## Quick start (local)

1) Create a virtual environment and install deps
```powershell
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r config/requirements.txt
```

2) Train a model (uses training_data.csv if available)
```powershell
python src/ml/azure_ml_pipeline.py
```

3) Run the API
```powershell
uvicorn src.app.main:app --reload --port 8080
```

4) Test prediction
```powershell
Invoke-RestMethod -Uri http://localhost:8080/predict -Method POST -Body (
    '{"instances": [{
        "month": "2025-07-01",
        "total_files": 120000,
        "avg_file_size_mb": 1.2,
        "pct_pdf": 0.45,
        "pct_docx": 0.3,
        "pct_xlsx": 0.25,
        "archive_frequency_per_day": 320
    }]}'
) -ContentType 'application/json'
```

## Deployment

**Local Development:**
- Run FastAPI server locally: `uvicorn src.app.main:app --reload --port 8080`
- Test with PowerShell or curl
- Debug using VS Code or IDE

**Azure Deployment (Optional):**
- Register trained model to Azure ML: `python scripts/promote_model_to_azure.py`
- Deploy as Azure ML online endpoint
- Test endpoint: `python scripts/test_endpoint_production.py`

For detailed deployment instructions, see `docs/guides/`

## Configuration & Environment

All configuration files are in `config/`:
- `azure_config.json` - Azure resource settings
- `environment.yml` - Conda environment definition
- `pyproject.toml` - Python project metadata
- `requirements.txt` - Python dependencies

## Data

Training and test data are in `test_data/`:
- `training_data.csv` - Historical archive data for model training
- `archive-data.csv` - Sample archive records for testing
- `model/` - Trained model artifacts
- `prepared/` - Preprocessed datasets

## Tests

```powershell
pytest -q src/tests
```

Unit tests are located in `src/tests/` alongside the code they test.

## Data schema (features)

Model expects period-level aggregates per tenant or scope:
- month (YYYY-MM-01)
- total_files (int)
- avg_file_size_mb (float)
- pct_pdf, pct_docx, pct_xlsx (floats summing <= 1.0; other types implicitly 1 - sum)
- archive_frequency_per_day (float)

Targets (label columns during training):
- archived_gb_next_period (float)
- savings_gb_next_period (float)

If you don't have historical data yet, training will synthesize a small dataset to demonstrate the flow.

## MLflow tracking

By default, logs to a local `mlruns` folder (auto-generated). To use Azure ML tracking, set `MLFLOW_TRACKING_URI` and `MLFLOW_EXPERIMENT_NAME`, or configure via the Azure ML SDK. The code will honor standard MLflow env vars.

## Documentation

All documentation is in the `docs/` folder:
- **docs/getting-started/** - Quick start guides and setup instructions
- **docs/guides/** - Detailed how-to guides (data extraction, training, deployment)
- **docs/references/** - Reference documentation and best practices
- **docs/sql/** - SQL scripts for data extraction from SmartArchive database
- **docs/archived/** - Outdated documentation

## Next phases

- Streamlit UI for scenario simulation
- Azure ML pipelines for data prep, training, registration, and deployment
- Model/data drift monitoring with Azure ML monitoring or custom MLflow metrics

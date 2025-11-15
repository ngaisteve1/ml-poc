# SmartArchive ML POC - Command Reference

## All Commands Quick Reference

### Data Generation
```bash
# Generate synthetic SmartArchive data
python src/ml/pipeline_components/prepare_data.py --output_data ./test_data

# Generate with custom output directory
python src/ml/pipeline_components/prepare_data.py --output_data /path/to/output
```

### Model Training
```bash
# Windows (single line - RECOMMENDED)
python src/ml/pipeline_components/train_model.py --input_data ./test_data/data.csv --output_model ./test_data/model

# Linux/Mac (with line continuation)
python src/ml/pipeline_components/train_model.py \
  --input_data ./test_data/data.csv \
  --output_model ./test_data/model

# With custom number of trees (Windows)
python src/ml/pipeline_components/train_model.py --input_data ./test_data/data.csv --output_model ./test_data/model --n_estimators 200

# With custom number of trees (Linux/Mac)
python src/ml/pipeline_components/train_model.py \
  --input_data ./test_data/data.csv \
  --output_model ./test_data/model \
  --n_estimators 200

# With explicit metrics output (Windows)
python src/ml/pipeline_components/train_model.py --input_data ./test_data/data.csv --output_model ./test_data/model --metrics_output ./results/metrics.json

# With explicit metrics output (Linux/Mac)
python src/ml/pipeline_components/train_model.py \
  --input_data ./test_data/data.csv \
  --output_model ./test_data/model \
  --metrics_output ./results/metrics.json
```

### Model Registration
```bash
# Register model to MLflow and/or Azure ML
python src/ml/pipeline_components/register_model.py \
  --input_model ./test_data/model

# Register with custom model name
python src/ml/pipeline_components/register_model.py \
  --input_model ./test_data/model \
  --model_name "archive-forecasting-v2"
```

### Azure ML Pipeline
```bash
# Submit entire pipeline to Azure ML
python src/ml/azure_ml_pipeline.py

# Submit with specific compute size
export COMPUTE_SIZE=Standard_D2s_v3
python src/ml/azure_ml_pipeline.py
```

### MLflow Tracking
```bash
# Start MLflow UI locally
mlflow ui --backend-store-uri ./mlruns

# Start on specific port
mlflow ui --backend-store-uri ./mlruns --port 8080

# View experiments at: http://localhost:5000
```

### REST API
```bash
# Start prediction API
python src/app/main.py

# API runs on: http://localhost:8000
# Documentation: http://localhost:8000/docs
# Redoc: http://localhost:8000/redoc

# Make prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "month": 11,
    "year": 2025,
    "file_type_pdf": 0.35,
    "file_type_docx": 0.45,
    "file_type_xlsx": 0.15,
    "file_type_other": 0.05,
    "avg_file_size_mb": 2.5,
    "median_file_size_mb": 1.8
  }'
```

---

## Complete Workflow

### 1️⃣ Generate Data (2 min)
```bash
python src/ml/pipeline_components/prepare_data.py --output_data ./test_data
```

### 2️⃣ Train Model (5 min)
```bash
python src/ml/pipeline_components/train_model.py \
  --input_data ./test_data/data.csv \
  --output_model ./test_data/model
```

### 3️⃣ Register Model (1 min)
```bash
python src/ml/pipeline_components/register_model.py --input_model ./test_data/model
```

### 4️⃣ Start API (0 min setup)
```bash
python src/app/main.py
# Then open http://localhost:8000/docs in browser
```

### 5️⃣ View Results in MLflow (1 min)
```bash
mlflow ui --backend-store-uri ./mlruns
# Then open http://localhost:5000 in browser
```

---

## Environment Variables

```bash
# Azure ML workspace configuration
export SUBSCRIPTION_ID=<your-subscription-id>
export RESOURCE_GROUP=<your-resource-group>
export WORKSPACE_NAME=<your-workspace-name>

# Azure credentials
export AZURE_CLIENT_ID=<your-client-id>
export AZURE_CLIENT_SECRET=<your-client-secret>
export AZURE_TENANT_ID=<your-tenant-id>

# MLflow
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_EXPERIMENT_NAME=archive-forecasting
```

---

## File Arguments

| Command | Required Arguments | Optional Arguments |
|---------|-------------------|-------------------|
| prepare_data.py | `--output_data` | None |
| train_model.py | `--input_data`, `--output_model` | `--n_estimators`, `--metrics_output` |
| register_model.py | `--input_model` | `--model_name` |
| azure_ml_pipeline.py | None | None (uses azure_config.json) |

---

## Output Files

### After Data Generation
```
output_data/
└── data.csv                 ← 24 rows of synthetic data
```

### After Model Training
```
output_model/
├── model.pkl                ← Trained RandomForest model
├── scaler.pkl               ← Feature scaler
└── metrics.json             ← Performance metrics
```

### After Registration
```
mlruns/
└── [experiment tracking]    ← MLflow artifacts
```

---

## Error Messages & Solutions

| Error | Solution |
|-------|----------|
| "Module not found" | `pip install -r requirements.txt` |
| "No such file or directory" | Check file path exists or run data generation first |
| "Port 5000 already in use" | Use different port: `mlflow ui --port 8080` |
| "Azure credentials not found" | Set environment variables or use `az login` |
| "Port 8000 already in use" | Kill process: `lsof -i :8000` or use different port |

---

## Common Workflows

### Local Development Loop
```bash
# 1. Generate data
python src/ml/pipeline_components/prepare_data.py --output_data ./test

# 2. Train model
python src/ml/pipeline_components/train_model.py \
  --input_data ./test/data.csv \
  --output_model ./test/model

# 3. View results
mlflow ui --backend-store-uri ./mlruns

# 4. Iterate: modify prepare_data.py or train_model.py, then go to step 1
```

### Production Deployment
```bash
# 1. Configure Azure
# Edit azure_config.json with your workspace details

# 2. Submit pipeline to Azure ML
python src/ml/azure_ml_pipeline.py

# 3. Monitor in Azure Portal
# Link will be printed in output

# 4. Deploy model endpoint
# Instructions in AZURE_ML_PIPELINE_GUIDE.md
```

### Integration Testing
```bash
# 1. Train model
python src/ml/pipeline_components/train_model.py \
  --input_data ./test/data.csv \
  --output_model ./test/model

# 2. Start API
python src/app/main.py &

# 3. Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"month": 11, "year": 2025, ...}'

# 4. View API docs
# Open http://localhost:8000/docs
```

---

**Last Updated:** November 4, 2025  
**Status:** Complete & Tested

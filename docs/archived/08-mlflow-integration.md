# MLflow Integration Guide for ML POC

## Overview

MLflow is already running at **http://127.0.0.1:5000/**

This guide shows how to integrate MLflow with your ML POC to track experiments, metrics, and models.

## What is MLflow?

MLflow provides:
- 📊 **Experiment Tracking** - Track metrics, parameters, and results
- 🤖 **Model Registry** - Version and manage models
- 📈 **Performance Monitoring** - Compare runs and models
- 📦 **Model Packaging** - Bundle models with dependencies

## Quick Start (5 minutes)

### Step 1: Verify MLflow is Running
```bash
# Check if MLflow server is running
curl http://127.0.0.1:5000
# Should return HTML

# Or open browser
http://127.0.0.1:5000
```

### Step 2: Train Model with MLflow
```bash
python src/ml/train_with_mlflow.py
```

### Step 3: View Results
```bash
# Open browser
http://127.0.0.1:5000
```

**You'll see:**
- ✅ Experiment: "Archive-Forecast-ML-POC"
- ✅ Run with all metrics logged
- ✅ Model saved and registered
- ✅ Feature importance plots

## What Gets Tracked

### Parameters Logged
```
n_estimators: 100
max_depth: 20
min_samples_split: 5
min_samples_leaf: 2
test_size: 0.2
random_state: 42
```

### Metrics Logged
```
train_mae:  {value}
train_rmse: {value}
train_r2:   {value}
test_mae:   {value}
test_rmse:  {value}
test_r2:    {value}
```

### Artifacts Logged
```
model/                          # Trained model
feature_importance.png          # Feature importance plot
feature_importance.json         # Feature importance data
```

### Tags
```
model_type: MultiOutputRandomForest
data_type: archive_metrics
targets: volume_gb,storage_saved_gb
```

## Running the Training Script

### Default (uses mock data)
```bash
python src/ml/train_with_mlflow.py
```

Output:
```
✅ MLflow configured: http://127.0.0.1:5000
📊 Experiment: Archive-Forecast-ML-POC
✅ Loaded data: data/training_data.csv
📊 Shape: (24, 13)
✅ Features: 10 columns
✅ Targets: 2 columns
...
✅ Training complete!
📊 View results at: http://127.0.0.1:5000
📈 Experiment: Archive-Forecast-ML-POC
🏷️  Run ID: abc123def456
```

### Custom Options
```bash
# Use different data
python src/ml/train_with_mlflow.py --data-path data/my_data.csv

# Save model to different location
python src/ml/train_with_mlflow.py --out-dir my_models

# Use different experiment name
python src/ml/train_with_mlflow.py --experiment-name "my-experiment"

# Use remote MLflow server
python src/ml/train_with_mlflow.py --mlflow-uri http://remote-server:5000
```

## MLflow UI Tour

### 1. View Experiments
```
http://127.0.0.1:5000
└── Experiments list
    └── Archive-Forecast-ML-POC
        └── Run 1 (Click to view details)
```

### 2. View Run Details
Click on any run to see:
- **Parameters** - Hyperparameters used
- **Metrics** - Performance metrics (MAE, RMSE, R²)
- **Artifacts** - Saved model and plots
- **System Metrics** - CPU, memory usage
- **Tags** - Custom metadata

### 3. Compare Runs
- Select multiple runs
- Click "Compare"
- See metrics side-by-side
- Identify best performing run

### 4. View Model Registry
```
Registry → Models
└── Select model
    └── Stages: Staging, Production, Archived
```

## Integration Examples

### Example 1: Track Custom Metrics
```python
import mlflow

with mlflow.start_run():
    # Your training code...
    
    # Log custom metric
    mlflow.log_metric("custom_score", 0.95)
    
    # Log custom parameter
    mlflow.log_param("batch_size", 32)
```

### Example 2: Log Plots and Visualizations
```python
import mlflow
import matplotlib.pyplot as plt

with mlflow.start_run():
    # Your training code...
    
    # Create plot
    plt.figure()
    plt.plot(history)
    plt.savefig('training_history.png')
    
    # Log to MLflow
    mlflow.log_artifact('training_history.png')
```

### Example 3: Log Dataset Info
```python
import mlflow

with mlflow.start_run():
    # Log dataset info
    mlflow.log_param("dataset_rows", 1000)
    mlflow.log_param("dataset_features", 10)
    mlflow.log_param("target_variable", "volume_gb")
```

### Example 4: Log Model with Signature
```python
import mlflow
from mlflow.models.signature import infer_signature

with mlflow.start_run():
    # Train model...
    
    # Infer signature from data
    signature = infer_signature(X_train, y_train)
    
    # Log model with signature
    mlflow.sklearn.log_model(
        model, 
        "model",
        signature=signature
    )
```

## Workflow: Mock Data → Real Data

### Phase 1: Development with Mock Data
```bash
# 1. Generate mock data
python src/ml/generate_mock_data.py

# 2. Train with MLflow tracking
python src/ml/train_with_mlflow.py

# 3. View results in MLflow UI
http://127.0.0.1:5000

# 4. Compare metrics
# 5. Iterate and improve
```

### Phase 2: Validation with Production Data
```bash
# 1. Extract production data (when ready)
# Run Query 10: setup/02-data-extraction.sql

# 2. Train with production data
python src/ml/train_with_mlflow.py --data-path data/production_data.csv

# 3. Compare mock vs production runs
# in MLflow UI

# 4. If satisfied, promote to production
```

## Monitoring Model Performance

### Track Performance Over Time
```bash
# Monthly retraining workflow
1. Extract new month data (Query 10)
2. Train: python src/ml/train_with_mlflow.py
3. View new run in MLflow
4. Compare with previous runs
5. If better: update production model
```

### Compare Runs
```
MLflow UI
→ Experiments
→ Archive-Forecast-ML-POC
→ Select Run 1 and Run 2
→ Click "Compare" button
→ View metrics side-by-side
```

## Model Registry (Advanced)

### Register Model
```python
import mlflow

with mlflow.start_run() as run:
    # Your training...
    mlflow.sklearn.log_model(model, "model")
    
    # Register model
    mlflow.register_model(
        f"runs:/{run.info.run_id}/model",
        "archive-forecast"
    )
```

### Promote Model to Production
```
MLflow UI
→ Models
→ archive-forecast
→ Select version
→ Stage: Staging → Production
```

### Load Model from Registry
```python
import mlflow

# Load from registry
model = mlflow.pyfunc.load_model("models:/archive-forecast/Production")

# Make predictions
predictions = model.predict(data)
```

## Troubleshooting

### MLflow Server Not Responding
```bash
# Check if server is running
curl http://127.0.0.1:5000

# If not, start it
mlflow ui --host 127.0.0.1 --port 5000
```

### Runs Not Showing in UI
```python
# Verify MLflow tracking URI
import mlflow
print(mlflow.get_tracking_uri())

# Should output: http://127.0.0.1:5000
```

### Import Error
```bash
# Install MLflow if missing
pip install mlflow

# Or update requirements
pip install -r requirements.txt
```

### Port 5000 Already in Use
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (get PID from above)
taskkill /PID <PID> /F

# Or use different port
mlflow ui --port 5001
```

## Best Practices

### 1. Use Meaningful Experiment Names
```python
experiment_name = f"archive-forecast-{datetime.now().strftime('%Y-%m-%d')}"
mlflow.set_experiment(experiment_name)
```

### 2. Tag Runs for Easy Filtering
```python
mlflow.set_tag("env", "development")
mlflow.set_tag("team", "data-science")
mlflow.set_tag("status", "experimental")
```

### 3. Log Data Info
```python
mlflow.log_param("dataset_version", "v1.0")
mlflow.log_param("data_source", "query_10")
mlflow.log_param("feature_set", "basic")
```

### 4. Use Run Names
```python
with mlflow.start_run(run_name="rf-100-trees-depth-20"):
    # Training code...
```

### 5. Compare Before Deploying
```bash
# Always compare runs before production
1. Train multiple versions
2. View all runs in MLflow
3. Compare metrics
4. Deploy best performer
```

## File Locations

```
ml-poc/
├── src/ml/
│   ├── train_with_mlflow.py ......... Training with MLflow
│   ├── train.py .................... Original training script
│   ├── generate_mock_data.py ....... Mock data generator
│   └── data_preprocessing.py ....... Data utilities
├── data/
│   └── training_data.csv ........... Mock data (generated)
├── models/
│   └── model.joblib ............... Saved model (generated)
└── mlruns/
    └── (MLflow internal directory)
```

## Next Steps

1. ✅ **Right Now:** `python src/ml/train_with_mlflow.py`
2. ✅ **View Results:** http://127.0.0.1:5000
3. ✅ **Compare Runs:** Select multiple runs in UI
4. ✅ **Export Model:** Download from MLflow registry
5. ✅ **Deploy:** Use saved model in API

## Additional Resources

- MLflow Documentation: https://mlflow.org/docs/
- MLflow GitHub: https://github.com/mlflow/mlflow
- Experiment Tracking Best Practices: https://mlflow.org/docs/latest/tracking/
- Model Registry Guide: https://mlflow.org/docs/latest/model-registry/

---

**Your ML experiments are now tracked, versioned, and easy to compare!** 📊✨

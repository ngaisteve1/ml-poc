# MLflow Integration - Quick Start

## ✅ MLflow is Ready!

Your MLflow server is running at: **http://127.0.0.1:5000/**

## One-Command Training with MLflow

```bash
python src/ml/train_with_mlflow.py
```

**Output:**
```
✅ MLflow configured: http://127.0.0.1:5000
📊 Experiment: Archive-Forecast-ML-POC
✅ Loaded data: data/training_data.csv
...
✅ Training complete!
📊 View results at: http://127.0.0.1:5000
📈 Experiment: Archive-Forecast-ML-POC
🏷️  Run ID: 50a0a1b8e7b54f25b16d5175d51d14fb
```

## View Results in MLflow UI

1. Open: **http://127.0.0.1:5000**
2. Click: **Archive-Forecast-ML-POC** experiment
3. Click: Latest run
4. See:
   - ✅ Parameters (n_estimators, max_depth, etc.)
   - ✅ Metrics (MAE, RMSE, R²)
   - ✅ Artifacts (model, plots, feature importance)
   - ✅ Model ready for deployment

## What's Tracked

### Metrics
```
train_mae:  1.5489    ← Training error
train_r2:   0.9538    ← Training fit
test_mae:   6.0619    ← Test error
test_r2:    0.7541    ← Test fit
```

### Artifacts
```
model/                  ← Trained sklearn model
feature_importance.png  ← Feature importance plot
feature_importance.json ← Feature data
```

### Parameters
```
n_estimators: 100
max_depth: 20
test_size: 0.2
random_state: 42
```

## Training Options

### Use Different Data
```bash
python src/ml/train_with_mlflow.py --data-path data/my_data.csv
```

### Custom Experiment Name
```bash
python src/ml/train_with_mlflow.py --experiment-name "my-experiment"
```

### Save to Different Location
```bash
python src/ml/train_with_mlflow.py --out-dir my_models
```

### Remote MLflow Server
```bash
python src/ml/train_with_mlflow.py --mlflow-uri http://remote-server:5000
```

## Compare Multiple Runs

1. Train multiple times with different parameters
2. In MLflow UI: Select 2+ runs
3. Click "Compare"
4. See side-by-side metrics
5. Choose best model

## Workflow

```
1. Generate data
   python src/ml/generate_mock_data.py

2. Train with MLflow
   python src/ml/train_with_mlflow.py

3. View results
   http://127.0.0.1:5000

4. Compare experiments
   Select runs in UI

5. Use best model
   models/model.joblib
```

## Next Steps

- ✅ **Now:** `python src/ml/train_with_mlflow.py`
- ✅ **View:** http://127.0.0.1:5000
- ✅ **Read:** `docs/08-mlflow-integration.md` for advanced usage
- ✅ **Deploy:** Use saved model in API

---

**Your experiments are now tracked and versioned!** 📊

# Complete ML POC Workflow with MLflow

## End-to-End Tutorial

### Phase 1: Generate Mock Data (1 minute)

```bash
python src/ml/generate_mock_data.py
```

✅ Output: `data/training_data.csv` with 24 months of realistic data

### Phase 2: Train Model with MLflow (1 minute)

```bash
python src/ml/train_with_mlflow.py
```

✅ Output: 
- Model saved to `models/model.joblib`
- Experiment logged to MLflow
- Run ID displayed in console

### Phase 3: View Results in MLflow (30 seconds)

1. Open: http://127.0.0.1:5000
2. Click: **Archive-Forecast-ML-POC** experiment
3. Click: Latest run
4. Explore:
   - Parameters tab: Hyperparameters used
   - Metrics tab: Performance metrics (MAE, RMSE, R²)
   - Artifacts tab: Saved model and plots
   - System tab: Training time, memory, CPU

### Phase 4: Run Multiple Experiments (Optional)

```bash
# Try with different parameters by editing the script
# Or generate different data
python src/ml/generate_mock_data.py --seed 999
python src/ml/train_with_mlflow.py

# Compare runs in MLflow UI
# Select Run 1 and Run 2 → Click "Compare"
```

### Phase 5: Use Trained Model

```python
import joblib
import pandas as pd

# Load model
model = joblib.load('models/model.joblib')

# Make predictions
new_data = pd.DataFrame({
    'files_archived': [15000],
    'avg_file_size_mb': [5.5],
    'largest_file_mb': [45],
    'pct_pdf': [0.40],
    'pct_docx': [0.30],
    'pct_xlsx': [0.20],
    'archive_frequency_per_day': [160],
    'deleted_files_count': [10500],
    'tenant_count': [20],
    'site_count': [120]
})

predictions = model.predict(new_data)
print(f"Predicted volume: {predictions[0][0]:.2f} GB")
print(f"Predicted savings: {predictions[0][1]:.2f} GB")
```

## Quick Reference Commands

```bash
# 1. Generate mock data
python src/ml/generate_mock_data.py [--rows 36] [--seed 999]

# 2. Train with MLflow (uses mock data automatically)
python src/ml/train_with_mlflow.py [--experiment-name "my-exp"]

# 3. View MLflow UI
# Open: http://127.0.0.1:5000

# 4. Load saved model
python -c "import joblib; m = joblib.load('models/model.joblib'); print(m)"
```

## File Organization

```
ml-poc/
├── 📊 Data & Models
│   ├── data/
│   │   └── training_data.csv .................. Generated/exported CSV
│   └── models/
│       └── model.joblib ..................... Trained model
│
├── 🔧 Source Code
│   └── src/ml/
│       ├── generate_mock_data.py ........... Mock data generator
│       ├── train_with_mlflow.py ........... Training with MLflow ⭐
│       ├── train.py ........................ Original training
│       ├── data_preprocessing.py .......... Utilities
│       └── monitor.py ..................... Monitoring
│
├── 📚 Documentation
│   └── docs/
│       ├── 01-start-here.md .............. Quick start
│       ├── 07-mock-data-guide.md ......... Mock data
│       └── 08-mlflow-integration.md ..... MLflow guide ⭐
│
├── 🗂️ Database Setup
│   └── setup/
│       ├── 01-create-indexes.sql ........ Index creation
│       └── 02-data-extraction.sql ...... Query 10
│
└── 📖 Quick References
    ├── MLFLOW_QUICKSTART.txt ........... MLflow summary
    └── MOCK_DATA_READY.txt ............. Mock data summary
```

## Workflow Timeline

```
Step 1: Generate Mock Data
Time: 1 minute
Command: python src/ml/generate_mock_data.py
Output: data/training_data.csv

        ↓

Step 2: Train Model with MLflow
Time: 2 minutes
Command: python src/ml/train_with_mlflow.py
Output: 
  - models/model.joblib
  - Experiment logged to MLflow
  - Run ID: abc123...

        ↓

Step 3: View in MLflow UI
Time: 30 seconds
URL: http://127.0.0.1:5000
View: Experiments → Archive-Forecast-ML-POC → Latest Run

        ↓

Step 4: Compare & Evaluate
Time: 5 minutes
Action: Compare metrics with other runs
Decide: Is model good enough?

        ↓

Step 5: Deploy Model
Time: 1 minute
Action: Use models/model.joblib in API or batch jobs
Result: Predictions in production
```

## MLflow UI Navigation

### View All Experiments
```
MLflow Home → Experiments
  └── Archive-Forecast-ML-POC (click to view)
      ├── Run 1 (date/time)
      ├── Run 2 (date/time)
      └── Run 3 (date/time)
```

### View Run Details
```
Click Run → Details
  ├── Parameters (n_estimators, max_depth, etc.)
  ├── Metrics (test_mae, test_rmse, test_r2)
  ├── Artifacts
  │   ├── model/
  │   ├── feature_importance.png
  │   └── feature_importance.json
  └── System (duration, CPU, memory)
```

### Compare Multiple Runs
```
Select Run 1 checkbox
Select Run 2 checkbox
Click "Compare" button
  └── Side-by-side metrics comparison
      ├── Parameters: Same? Different?
      └── Metrics: Which is better?
```

## Performance Expectations

### Training Time
- Mock data (24 rows): ~2 seconds
- Production data (1000 rows): ~5 seconds
- Large dataset (10000 rows): ~10 seconds

### Model Performance
- Train MAE: 1-2 GB (mock data)
- Test MAE: 5-8 GB (mock data)
- Train R²: 0.95+ (mock data)
- Test R²: 0.75+ (mock data)

### MLflow Logging
- Metrics: <1 second
- Model: 5-10 seconds
- Artifacts: 2-5 seconds
- Total overhead: ~10 seconds

## Troubleshooting

### MLflow UI Not Responding
```bash
# Check server
curl http://127.0.0.1:5000

# Restart if needed
mlflow ui --host 127.0.0.1 --port 5000
```

### Runs Not Showing
```python
import mlflow
print(mlflow.get_tracking_uri())
# Should output: http://127.0.0.1:5000
```

### Import Error
```bash
pip install mlflow matplotlib
```

### Model Not Saving
```bash
# Ensure models directory exists
mkdir models
python src/ml/train_with_mlflow.py
```

## Next Steps

1. ✅ **Now:** Generate data and train
   ```bash
   python src/ml/generate_mock_data.py
   python src/ml/train_with_mlflow.py
   ```

2. ✅ **View:** Open MLflow UI
   ```
   http://127.0.0.1:5000
   ```

3. ✅ **Explore:** Click through experiments and runs

4. ✅ **Compare:** Train multiple times, compare results

5. ✅ **Deploy:** Use best model in production

## Advanced: Automated Training Pipeline

```bash
#!/bin/bash
# train_pipeline.sh - Automated training workflow

echo "1. Generating mock data..."
python src/ml/generate_mock_data.py

echo "2. Training multiple versions..."
for seed in 42 123 999; do
  echo "  Training with seed $seed..."
  python src/ml/generate_mock_data.py --seed $seed
  python src/ml/train_with_mlflow.py --experiment-name "seed-$seed"
done

echo "3. Training complete!"
echo "4. View results at: http://127.0.0.1:5000"
```

## Key Commands Cheat Sheet

```bash
# Generate data
python src/ml/generate_mock_data.py

# Train model
python src/ml/train_with_mlflow.py

# View MLflow
http://127.0.0.1:5000

# Load model in Python
import joblib
model = joblib.load('models/model.joblib')

# Make predictions
predictions = model.predict(X_new)
```

---

**Complete ML POC workflow: Data → Training → Tracking → Deployment** ✨

From mock data to production model in 5 minutes! 🚀

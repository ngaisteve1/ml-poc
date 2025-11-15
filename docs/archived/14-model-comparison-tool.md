# Model Comparison Tool Guide

**File**: `src/ml/compare_models.py`

**Purpose**: Automatically compare all models in your MLflow experiment and rank them by quality.

---

## Quick Start

```bash
# Compare all models in the experiment
python src/ml/compare_models.py

# Compare top 3 models
python src/ml/compare_models.py --top 3

# Use a different experiment name
python src/ml/compare_models.py --experiment-name "my-custom-experiment"

# Use different MLflow server
python src/ml/compare_models.py --mlflow-uri "http://your-server:5000"
```

---

## What It Does

The tool automatically:

1. **Fetches all runs** from your MLflow experiment
2. **Extracts key metrics** (Test R², Test MAE, Test RMSE, Train R², Train MAE)
3. **Calculates overfitting** (train R² - test R²)
4. **Scores each model** (1-5 points per metric, 0-23 total)
5. **Ranks models** by score (highest first)
6. **Shows best model** with detailed analysis
7. **Provides recommendations** for next steps

---

## Output Example

```
MODEL COMPARISON RESULTS
================================================================================

Ranking:
Rank  Run ID      Test R²    Test MAE     Test RMSE    Overfit    Score
─────────────────────────────────────────────────────────────────────────────
1     a1b2c3d4    0.8543     5.21 GB      7.89 GB      0.1234     23/23 ⭐⭐⭐⭐⭐
2     e5f6g7h8    0.7541     6.06 GB      8.91 GB      0.2000     19/23 ⭐⭐⭐⭐
3     i9j0k1l2    0.6234     12.45 GB    15.67 GB      0.3200     12/23 ⭐⭐
─────────────────────────────────────────────────────────────────────────────

🏆 BEST MODEL
================================================================================

Run ID: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

Metrics:
  Test R²:   0.8543 ✅
  Test MAE:  5.21 GB ✅
  Test RMSE: 7.89 GB
  Train R²:  0.9777
  Train MAE: 3.45 GB

Overfitting:
  R² Gap: 0.1234 ✅ (< 0.20, good)
  MAE Ratio: 0.64x ✅ (< 5x, good)

Training Time: 2.3 seconds
Score: 23/23 ⭐⭐⭐⭐⭐

================================================================================

📋 RECOMMENDATIONS:
✅ Test R² is excellent. Model is ready for use.
✅ Test MAE (5.21 GB) is acceptable.
✅ Overfitting is minimal. Good generalization expected.

📌 Next Steps:
   1. Model ready at: models/model.joblib
   2. Use in API or batch predictions
   3. Validate with production data (when ready)
   4. Set up monthly retraining with new data
```

---

## Scoring System

The tool scores each model on 5 dimensions:

### 1. **Test R² (5 points max)**
Explains how much variance the model captures
- > 0.80: ⭐⭐⭐⭐⭐ (5 pts) - Excellent
- > 0.75: ⭐⭐⭐⭐ (4 pts) - Good
- > 0.70: ⭐⭐⭐ (3 pts) - Acceptable
- > 0.60: ⭐⭐ (2 pts) - Needs improvement
- ≤ 0.60: ⭐ (1 pt) - Poor

### 2. **Test MAE (5 points max)**
Mean Absolute Error in GB (lower is better)
- < 5 GB: ⭐⭐⭐⭐⭐ (5 pts) - Excellent
- < 8 GB: ⭐⭐⭐⭐ (4 pts) - Good
- < 10 GB: ⭐⭐⭐ (3 pts) - Acceptable
- < 15 GB: ⭐⭐ (2 pts) - Needs improvement
- ≥ 15 GB: ⭐ (1 pt) - Poor

### 3. **Test RMSE (5 points max)**
Root Mean Squared Error in GB (lower is better, penalizes large errors)
- < 8 GB: ⭐⭐⭐⭐⭐ (5 pts) - Excellent
- < 10 GB: ⭐⭐⭐⭐ (4 pts) - Good
- < 12 GB: ⭐⭐⭐ (3 pts) - Acceptable
- < 15 GB: ⭐⭐ (2 pts) - Needs improvement
- ≥ 15 GB: ⭐ (1 pt) - Poor

### 4. **Overfitting Score (5 points max)**
Difference between train R² and test R² (lower is better, indicates generalization)
- < 0.10: ⭐⭐⭐⭐⭐ (5 pts) - Perfect generalization
- < 0.15: ⭐⭐⭐⭐ (4 pts) - Excellent generalization
- < 0.20: ⭐⭐⭐ (3 pts) - Good generalization
- < 0.30: ⭐⭐ (2 pts) - Some overfitting
- ≥ 0.30: ⭐ (1 pt) - High overfitting

### 5. **Speed Score (3 points max)**
Training time in seconds (faster is better)
- < 5 sec: ⭐⭐⭐ (3 pts) - Very fast
- < 10 sec: ⭐⭐ (2 pts) - Fast
- ≥ 10 sec: ⭐ (1 pt) - Slow

**Total Score: 0-23 points**

---

## Decision Rules

The tool uses this logic to determine "best model":

1. **Highest Score Wins** - Model with most points is ranked first
2. **Ties Are Broken By**:
   - Test R² (higher is better)
   - Test MAE (lower is better)
   - Overfitting (lower is better)

---

## Integration with Your Workflow

### After Training Models:
```bash
# Train model 1
python src/ml/train_with_mlflow.py

# Train model 2 with different parameters
python src/ml/train_with_mlflow.py

# Train model 3 with more data
python src/ml/generate_mock_data.py --rows 48
python src/ml/train_with_mlflow.py

# Compare all three
python src/ml/compare_models.py
```

### After Experiment:
```bash
# View top 5 models
python src/ml/compare_models.py --top 5

# Identify best model (highest score)
# Use that model for deployment
```

---

## Example: Comparing 3 Models

**Scenario**: You've trained 3 different models trying different hyperparameters.

```bash
$ python src/ml/compare_models.py
✅ Connected to MLflow: http://127.0.0.1:5000
✅ Found 3 runs

MODEL COMPARISON RESULTS

Rank  Run ID      Test R²    Test MAE      Test RMSE    Overfit    Score
─────────────────────────────────────────────────────────────────────────────
1     abc123      0.8200     7.34 GB       10.56 GB     0.1500     20/23 ⭐⭐⭐⭐
2     def456      0.8100     7.89 GB       11.23 GB     0.1900     19/23 ⭐⭐⭐⭐
3     ghi789      0.7200     12.50 GB      18.90 GB     0.2800     12/23 ⭐⭐

🏆 BEST MODEL: abc123
   Test R²: 0.8200 ✅
   Test MAE: 7.34 GB ✅
   Score: 20/23

📋 RECOMMENDATIONS:
✅ Test R² is good. Model is production-ready.
```

**Decision**: Use model `abc123` (highest score, best R² and MAE).

---

## Common Questions

### Q: "Why is Model A ranked lower but has lower MAE?"
**A**: The tool considers multiple factors. Model B might have:
- Higher R² (explains more variance)
- Better overfitting score (generalizes better)
- These factors outweigh slightly higher MAE

### Q: "Can I use a different scoring system?"
**A**: Yes! Edit `calculate_score()` function to adjust thresholds:
```python
# Change this threshold:
if mae < 5:  # Currently < 5 GB gets 5 points
    breakdown['test_mae_score'] = 5
```

### Q: "How do I run this on production models?"
**A**: Point it to your production experiment:
```bash
python src/ml/compare_models.py \
  --experiment-name "production-models" \
  --mlflow-uri "http://prod-server:5000"
```

### Q: "Which metric is most important?"
**A**: Priority order (configurable):
1. **Test R²** (5 pts) - Must explain variance well
2. **Test MAE** (5 pts) - Prediction accuracy
3. **Test RMSE** (5 pts) - Handles large errors
4. **Overfitting** (5 pts) - Generalization ability
5. **Speed** (3 pts) - Training efficiency

### Q: "Can I compare runs manually in MLflow UI instead?"
**A**: Yes! But this tool:
- Automatically calculates scores
- Ranks all models at once
- Provides recommendations
- Faster than clicking through UI

---

## Troubleshooting

### Issue: "Experiment 'Archive-Forecast-ML-POC' not found"
```bash
# Check your experiment name
python src/ml/compare_models.py --experiment-name "actual-name"
```

### Issue: "No completed runs with metrics found"
```bash
# Make sure you've trained at least one model:
python src/ml/train_with_mlflow.py

# Then run comparison:
python src/ml/compare_models.py
```

### Issue: "Connection refused" to MLflow
```bash
# Make sure MLflow is running:
mlflow ui --host 127.0.0.1 --port 5000

# In another terminal, run the comparison:
python src/ml/compare_models.py
```

---

## Next Steps

1. **Train multiple models** with different parameters
2. **Run comparison** to find best one
3. **Review recommendations** for production readiness
4. **Export best model** from MLflow
5. **Deploy** to your application
6. **Monitor** predictions in production
7. **Retrain monthly** with new data

---

## Files Referenced

- Input: Runs from MLflow experiment
- Output: Console table, rankings, recommendations
- Model saved at: `models/model.joblib`
- Logs saved at: MLflow artifacts

---

## Related Documentation

- 📖 **docs/13-model-selection.md** - Manual decision framework
- 📖 **docs/08-mlflow-integration.md** - MLflow setup guide
- 📖 **docs/09-complete-workflow.md** - End-to-end workflow
- 🐍 **src/ml/train_with_mlflow.py** - Training script
- 🐍 **src/ml/generate_mock_data.py** - Mock data generator

---

**Last Updated**: 2025-01-01  
**Version**: 1.0  
**Status**: ✅ Production Ready

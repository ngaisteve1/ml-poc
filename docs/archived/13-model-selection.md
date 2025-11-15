# How to Determine the Best Model

## Quick Decision Matrix

| Metric | What It Means | Target | Priority |
|--------|---------------|--------|----------|
| **Test R²** | How well model fits test data | > 0.75 | 🔴 HIGH |
| **Test MAE** | Average prediction error (GB) | < 10 | 🔴 HIGH |
| **Test RMSE** | Error considering large mistakes | < 15 | 🟠 MEDIUM |
| **Train vs Test Gap** | Overfitting indicator | Small | 🟠 MEDIUM |
| **Training Time** | Speed of model | < 10 sec | 🟡 LOW |

## Step 1: Compare in MLflow UI

### Open MLflow
```
http://127.0.0.1:5000
→ Experiments
→ Archive-Forecast-ML-POC
```

### Select Both Runs
```
☑️ Run 1 (model-1)
☑️ Run 2 (model-2)
Click: "Compare" button
```

---

## Step 2: Analyze Key Metrics

### Test R² (Most Important)
```
Higher is better: 0.75+

Model A: test_r2 = 0.8543 ✅ BETTER
Model B: test_r2 = 0.7541

→ Model A explains more variance in test data
```

### Test MAE (Most Important)
```
Lower is better: < 10 GB

Model A: test_mae = 5.2 GB ✅ BETTER
Model B: test_mae = 6.1 GB

→ Model A makes smaller prediction errors
```

### Test RMSE (Secondary)
```
Lower is better: < 15 GB

Model A: test_rmse = 7.8 GB ✅ BETTER
Model B: test_rmse = 8.9 GB

→ Model A handles large errors better
```

---

## Step 3: Check for Overfitting

### Compare Train vs Test Metrics

**Healthy Model (Low Overfitting):**
```
Train MAE:  1.5 GB
Test MAE:   6.0 GB
Gap: 4.5 GB  ✅ Reasonable (test is ~4x train)

Train R²: 0.95
Test R²:  0.75
Gap: 0.20  ✅ Acceptable
```

**Overfit Model (Red Flag):**
```
Train MAE:  0.5 GB
Test MAE:  15.0 GB
Gap: 14.5 GB  ⚠️ TOO LARGE (model memorized training)

Train R²: 0.98
Test R²:  0.50
Gap: 0.48  ⚠️ CONCERNING
```

---

## Complete Model Comparison Checklist

### ✅ Test Metrics (Most Important)
```
□ Test R² > 0.75         → Explains variance well
□ Test MAE < 10 GB       → Reasonable error
□ Test RMSE < 15 GB      → Handles outliers OK
```

### ✅ Overfitting Check (Important)
```
□ Train R² - Test R² < 0.25      → Not overfitting
□ Train MAE / Test MAE < 5x      → Reasonable gap
□ Validation loss plateaued       → Not improving
```

### ✅ Consistency (Nice to Have)
```
□ Train MAE low                   → Learns training data
□ Test metrics stable             → Consistent generalization
□ Training time reasonable        → < 30 seconds
```

---

## Real Example: Which Model to Choose?

### Scenario: Comparing 3 Models

```
MODEL A (seed=42):
  test_r2:   0.8543 ✅
  test_mae:  5.2 GB ✅
  test_rmse: 7.8 GB ✅
  train_r2:  0.9538
  train_mae: 1.5 GB
  overfitting: LOW ✅

MODEL B (seed=123):
  test_r2:   0.7541
  test_mae:  6.1 GB
  test_rmse: 8.9 GB
  train_r2:  0.9521
  train_mae: 1.5 GB
  overfitting: LOW ✅

MODEL C (seed=999):
  test_r2:   0.6234 ⚠️
  test_mae:  12.4 GB ⚠️
  test_rmse: 18.2 GB ⚠️
  train_r2:  0.9612
  train_mae: 1.2 GB
  overfitting: MEDIUM ⚠️
```

**🏆 BEST: Model A**
- Highest test R² (0.8543)
- Lowest test MAE (5.2 GB)
- Good overfitting balance
- Consistently best across all metrics

---

## Step-by-Step Guide in MLflow

### 1. Open Comparison View
```
MLflow UI
→ Experiments → Archive-Forecast-ML-POC
→ Select Run 1 ☑️
→ Select Run 2 ☑️
→ Click "Compare" button
```

### 2. View Metrics Table
```
Metrics Tab shows:
┌─────────────────┬────────┬────────┐
│ Metric          │ Run 1  │ Run 2  │
├─────────────────┼────────┼────────┤
│ test_r2         │ 0.854  │ 0.754  │
│ test_mae        │ 5.2    │ 6.1    │
│ test_rmse       │ 7.8    │ 8.9    │
│ train_r2        │ 0.954  │ 0.952  │
│ train_mae       │ 1.5    │ 1.5    │
└─────────────────┴────────┴────────┘
```

### 3. Analyze Differences
```
✅ Run 1 Better In: test_r2, test_mae, test_rmse
✅ Run 2 Better In: (none, Run 1 wins overall)
```

### 4. Make Decision
```
🏆 Choose Run 1 (best test metrics)
```

---

## Decision Framework: Flowchart

```
START: Comparing 2+ Models
    ↓
1. Look at Test R²
    ├─ R² > 0.80  → Continue ✅
    └─ R² < 0.70  → Eliminate model ❌
    ↓
2. Look at Test MAE
    ├─ MAE < 8 GB   → Continue ✅
    └─ MAE > 12 GB  → Eliminate model ❌
    ↓
3. Check Overfitting
    ├─ Train-Test gap < 0.25 → Continue ✅
    └─ Train-Test gap > 0.35 → Eliminate model ❌
    ↓
4. If Still Tied
    ├─ Choose: Lower training time
    ├─ Choose: More consistent metrics
    └─ Choose: Simpler parameters
    ↓
DECISION: Best Model Selected ✅
```

---

## Scoring System: Quantify Which is Best

### Assign Points (1-5)

```python
# For each metric, higher is better

MODEL A Scoring:
  test_r2 (0.8543):    5 points (excellent)
  test_mae (5.2 GB):   5 points (excellent)
  test_rmse (7.8 GB):  5 points (good)
  overfitting:         5 points (minimal)
  training_time:       4 points (reasonable)
  ────────────────────────────────
  TOTAL: 24/25 points  ⭐⭐⭐⭐⭐

MODEL B Scoring:
  test_r2 (0.7541):    3 points (acceptable)
  test_mae (6.1 GB):   4 points (good)
  test_rmse (8.9 GB):  4 points (good)
  overfitting:         4 points (low)
  training_time:       4 points (reasonable)
  ────────────────────────────────
  TOTAL: 19/25 points  ⭐⭐⭐⭐

🏆 WINNER: Model A (24 > 19)
```

---

## When Models are VERY Similar

### Example: Scores Differ by < 2 Points
```
Model A: 22/25 points
Model B: 21/25 points

→ Virtually equivalent, choose by:
  1. Training time (faster wins)
  2. Parameter simplicity (fewer hyperparams wins)
  3. Feature stability (consistent importance wins)
  4. Visual inspection (artifacts/plots)
```

---

## What Each Metric Really Means

### R² (Coefficient of Determination)
```
R² = 0.85 means:
  "Model explains 85% of variance in test data"
  
Interpretation:
  R² > 0.80  → Excellent fit
  R² 0.70-80 → Good fit
  R² 0.60-70 → Acceptable fit
  R² < 0.60  → Poor fit ❌

Example:
  Test R² = 0.8543  ✅ This model is very good
  Test R² = 0.5234  ❌ This model is not reliable
```

### MAE (Mean Absolute Error)
```
MAE = 5.2 GB means:
  "On average, predictions are off by ±5.2 GB"
  
Interpretation:
  If actual = 50 GB, prediction ≈ 44-56 GB
  
Lower is better:
  MAE < 5 GB   → Excellent accuracy
  MAE 5-10 GB  → Good accuracy
  MAE 10-20 GB → Acceptable
  MAE > 20 GB  → Poor ❌
```

### RMSE (Root Mean Squared Error)
```
RMSE = 7.8 GB means:
  "Error considering larger mistakes more heavily"
  
When to use:
  • When large errors are worse
  • When you want to penalize outliers
  
Comparison:
  RMSE > MAE always (penalizes big errors)
  If RMSE ≈ MAE → Errors are consistent
  If RMSE >> MAE → Some very large errors
```

---

## Common Pitfalls to Avoid

### ❌ Mistake 1: Only Looking at Training Metrics
```
WRONG: "Model A has train_r2=0.98, it's the best!"
RIGHT: Compare TEST metrics (generalization)
```

### ❌ Mistake 2: Ignoring Overfitting
```
WRONG: train_r2=0.99, test_r2=0.50
  ↓ Model memorized training data, won't generalize

RIGHT: train_r2=0.95, test_r2=0.80
  ↓ Healthy generalization
```

### ❌ Mistake 3: Focusing on Single Metric
```
WRONG: "Model A has higher MAE, so it's worse"
RIGHT: Consider all metrics: R², MAE, RMSE, overfitting

Example:
  Model A: test_r2=0.85, test_mae=6.5 ✅
  Model B: test_r2=0.70, test_mae=5.0 ❌ (overall worse)
```

### ❌ Mistake 4: Not Checking Statistical Significance
```
WRONG: "Model A=0.754, Model B=0.753, A is better"
RIGHT: Difference of 0.001 is noise, run multiple times

Solution: Train 3-5 times, compare averages
```

---

## Advanced: Statistical Comparison

### Run Multiple Times, Take Average

```bash
# Train with same data, different seeds
python src/ml/train_with_mlflow.py --experiment-name "model-a-v1"
python src/ml/train_with_mlflow.py --experiment-name "model-a-v2"
python src/ml/train_with_mlflow.py --experiment-name "model-a-v3"
```

### Compare Averages
```
Model A (3 runs):
  avg test_r²:   0.8543, 0.8521, 0.8535  → avg = 0.8533 ✅
  std dev:       0.0010 (very stable)

Model B (3 runs):
  avg test_r²:   0.7541, 0.7523, 0.7685  → avg = 0.7583
  std dev:       0.0082 (more variable)

→ Model A is more stable AND higher performing
```

---

## Final Decision: Best Model Checklist

### Before Selecting Best Model, Verify:

```
□ Test R² > 0.75
□ Test MAE < 10 GB
□ Train-Test gap < 0.25
□ No overfitting signs
□ Model trained on representative data
□ Multiple runs show consistency
□ Error distribution looks reasonable
□ Business requirements met
```

### If ALL ✅:
```
→ Model is READY FOR PRODUCTION
```

### If ANY ❌:
```
→ Retrain with different parameters
→ Get more data
→ Engineer better features
```

---

## Your Next Steps

### 1. Compare Your 2 Models Right Now
```
MLflow UI → Compare
Identify: Which has higher test_r2?
```

### 2. Calculate the Scoring
```
Use the scoring table above
Count total points
Winner: Higher score
```

### 3. Check Overfitting
```
train_r2 - test_r2 = ?
  < 0.20  ✅ Good
  0.20-30 ⚠️ Watch
  > 0.30  ❌ Retrain
```

### 4. Make Final Decision
```
Select best model
Note: Run ID
Location: models/model.joblib
```

### 5. Document Decision
```
Why this model won:
  • Higher test R²
  • Lower test MAE
  • Minimal overfitting
  • Consistent metrics
```

---

## Example Output Format

```
COMPARISON RESULTS
==================

Run 1 (seed=42):
  Test R²:   0.8543
  Test MAE:  5.2 GB
  Overfitting: 0.13 (good)
  Score: ⭐⭐⭐⭐⭐ (24/25)

Run 2 (seed=123):
  Test R²:   0.7541
  Test MAE:  6.1 GB
  Overfitting: 0.14 (good)
  Score: ⭐⭐⭐⭐ (19/25)

WINNER: Run 1 ✅
Reason: Higher test R², lower test MAE
Next Step: Deploy models/model.joblib
```

---

**Key Takeaway: Compare test metrics, check overfitting, then decide based on overall performance!** 🎯

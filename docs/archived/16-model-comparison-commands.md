╔══════════════════════════════════════════════════════════════════════════════╗
║                   MODEL COMPARISON TOOL - QUICK COMMANDS                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 MOST COMMON USE:
─────────────────────────────────────────────────────────────────────────────
After training your models in MLflow, compare them automatically:

    python src/ml/compare_models.py

This will:
  ✅ Fetch all your trained models
  ✅ Calculate quality scores (1-23 points total)
  ✅ Rank them automatically
  ✅ Show best model with analysis
  ✅ Provide recommendations


📊 WHAT YOU'LL SEE:
─────────────────────────────────────────────────────────────────────────────

MODEL COMPARISON RESULTS
================================================================================

Ranking:
Rank  Run ID      Test R²    Test MAE     Test RMSE    Overfit    Score
─────────────────────────────────────────────────────────────────────────────
1     abc123      0.8543     5.21 GB      7.89 GB      0.1234     23/23 ⭐⭐⭐⭐⭐
2     def456      0.7541     6.06 GB      8.91 GB      0.2000     19/23 ⭐⭐⭐⭐

🏆 BEST MODEL
─────────────────────────────────────────────────────────────────────────────
Run ID: abc123e5f6g7h8i9j0k1l2m3n4o5p6
Test R²: 0.8543 ✅
Test MAE: 5.21 GB ✅
Score: 23/23 ⭐⭐⭐⭐⭐


🔧 OTHER COMMANDS:
─────────────────────────────────────────────────────────────────────────────

# View only top 3 models
python src/ml/compare_models.py --top 3

# Use different experiment name
python src/ml/compare_models.py --experiment-name "my-experiment"

# Connect to different MLflow server
python src/ml/compare_models.py --mlflow-uri "http://other-server:5000"

# Combine options
python src/ml/compare_models.py --top 5 --experiment-name "production" --mlflow-uri "http://prod:5000"


📈 WORKFLOW EXAMPLE:
─────────────────────────────────────────────────────────────────────────────

Step 1: Train first model
$ python src/ml/train_with_mlflow.py
✅ Logged to MLflow (Run: abc123)

Step 2: Train second model with different parameters
$ python src/ml/train_with_mlflow.py
✅ Logged to MLflow (Run: def456)

Step 3: Compare models
$ python src/ml/compare_models.py
┌─────────────────────────────────────────────────────┐
│ MODEL COMPARISON RESULTS                            │
│                                                     │
│ 1. abc123 - 23/23 ⭐⭐⭐⭐⭐ BEST MODEL (USE THIS)  │
│ 2. def456 - 19/23 ⭐⭐⭐⭐                          │
└─────────────────────────────────────────────────────┘

Step 4: Model at models/model.joblib is ready for deployment


⭐ KEY METRICS EXPLAINED:
─────────────────────────────────────────────────────────────────────────────

Test R² (Coefficient of Determination)
  ├─ What: How much variance does model explain?
  ├─ Range: 0.0 to 1.0
  ├─ Better: HIGHER is better
  ├─ Points: >0.80 = 5 pts ⭐⭐⭐⭐⭐, >0.75 = 4 pts, >0.70 = 3 pts
  └─ Target: > 0.75 ✅

Test MAE (Mean Absolute Error)
  ├─ What: Average prediction error in GB
  ├─ Example: 5.21 GB means predictions off by ~5 GB on average
  ├─ Better: LOWER is better
  ├─ Points: <5 GB = 5 pts ⭐⭐⭐⭐⭐, <8 GB = 4 pts, <10 GB = 3 pts
  └─ Target: < 10 GB ✅

Test RMSE (Root Mean Squared Error)
  ├─ What: Like MAE but penalizes large errors more
  ├─ Better: LOWER is better
  ├─ Points: <8 GB = 5 pts, <10 GB = 4 pts, <12 GB = 3 pts
  └─ Target: < 12 GB ✅

Overfitting (Train R² - Test R²)
  ├─ What: Is model memorizing training data?
  ├─ Good: SMALL gap (<0.20) = generalizes well
  ├─ Bad: BIG gap (>0.30) = overfits to training data
  ├─ Points: <0.10 gap = 5 pts ⭐⭐⭐⭐⭐, <0.20 = 3 pts
  └─ Example: gap of 0.1234 = Good ✅


✅ SCORING SYSTEM (Total: 0-23 Points):
─────────────────────────────────────────────────────────────────────────────

  Metric             | Max Points | Threshold for Full Points
─────────────────────────────────────────────────────────────
  Test R²            |     5      | > 0.80
  Test MAE           |     5      | < 5 GB
  Test RMSE          |     5      | < 8 GB
  Overfitting        |     5      | Gap < 0.10
  Speed (optional)   |     3      | < 5 seconds
─────────────────────────────────────────────────────────────
  TOTAL              |    23      |

Score Interpretation:
  20-23: ⭐⭐⭐⭐⭐ Excellent - Production ready
  17-19: ⭐⭐⭐⭐ Good - Production ready with monitoring
  14-16: ⭐⭐⭐ Acceptable - Needs improvement
  11-13: ⭐⭐ Poor - Needs significant work
   0-10: ⭐ Very Poor - Not recommended


🎓 EXAMPLE: COMPARING 3 MODELS:
─────────────────────────────────────────────────────────────────────────────

You train 3 models with different hyperparameters:

Model A (n_estimators=100, max_depth=10)
  Test R²: 0.8543 (5 pts)
  Test MAE: 5.21 GB (5 pts)
  Test RMSE: 7.89 GB (5 pts)
  Overfit: 0.1234 (3 pts)
  Speed: 2.3 sec (3 pts)
  ────────────────────────
  TOTAL: 21/23 pts ⭐⭐⭐⭐⭐

Model B (n_estimators=50, max_depth=5)
  Test R²: 0.7541 (4 pts)
  Test MAE: 6.06 GB (4 pts)
  Test RMSE: 8.91 GB (4 pts)
  Overfit: 0.2000 (2 pts)
  Speed: 1.2 sec (3 pts)
  ────────────────────────
  TOTAL: 17/23 pts ⭐⭐⭐⭐

Model C (n_estimators=200, max_depth=15)
  Test R²: 0.7200 (3 pts)
  Test MAE: 8.50 GB (3 pts)
  Test RMSE: 12.30 GB (3 pts)
  Overfit: 0.3500 (1 pt)
  Speed: 5.1 sec (2 pts)
  ────────────────────────
  TOTAL: 12/23 pts ⭐⭐

🏆 WINNER: Model A (21 pts) ← USE THIS FOR PRODUCTION


❓ COMMON QUESTIONS:
─────────────────────────────────────────────────────────────────────────────

Q: "My best model scored 18/23. Is it good enough?"
A: Yes! Score >15 is production-ready. This scores 18 = Good.
   Test R²=0.77 and Test MAE=8 GB are acceptable thresholds.

Q: "Two models have same score. Which to pick?"
A: Tiebreaker order:
   1. Higher Test R² (explains more variance)
   2. Lower Test MAE (more accurate)
   3. Lower overfitting (better generalization)
   4. Faster training (lower operational cost)

Q: "What if all models score poorly (<12)?"
A: Your model needs improvement:
   1. Get more data: python src/ml/generate_mock_data.py --rows 48
   2. Try new features: edit train_with_mlflow.py
   3. Different algorithm: use different sklearn models
   4. Hyperparameter tuning: adjust max_depth, n_estimators, etc.

Q: "Can I modify the scoring thresholds?"
A: Yes! Edit compare_models.py calculate_score() function:
   
   if r2 > 0.75:  # Change 0.75 to your threshold
       breakdown['test_r2_score'] = 4

Q: "How often should I retrain?"
A: After major data changes or monthly, whichever comes first.
   1. Generate new data: python src/ml/generate_mock_data.py
   2. Train new model: python src/ml/train_with_mlflow.py
   3. Compare models: python src/ml/compare_models.py
   4. Deploy best one if score > current production model

Q: "Can I use this with production data?"
A: Yes! Just ensure data is in same format as training_data.csv:
   - Columns: period, files_archived, volume_gb, ... (13 total)
   - Format: CSV with headers
   - Location: data/training_data.csv


🚀 NEXT STEPS:
─────────────────────────────────────────────────────────────────────────────

1. Generate mock data:
   python src/ml/generate_mock_data.py --rows 24

2. Train models (run multiple times):
   python src/ml/train_with_mlflow.py
   python src/ml/train_with_mlflow.py
   python src/ml/train_with_mlflow.py

3. Compare them:
   python src/ml/compare_models.py

4. Pick winner and deploy to production

5. Monitor performance, retrain monthly


📖 RELATED DOCUMENTATION:
─────────────────────────────────────────────────────────────────────────────

For more details, see:
  • docs/13-model-selection.md - Manual decision framework
  • docs/14-model-comparison-tool.md - Full tool documentation
  • docs/08-mlflow-integration.md - MLflow setup guide
  • docs/09-complete-workflow.md - End-to-end workflow

For more help:
  • Check MLflow UI: http://127.0.0.1:5000
  • Review model artifacts and metrics
  • Compare runs side-by-side


✨ TIPS & TRICKS:
─────────────────────────────────────────────────────────────────────────────

💡 Keep MLflow UI open while comparing:
   http://127.0.0.1:5000 → Models tab → Compare runs

💡 Export comparison results:
   python src/ml/compare_models.py > model_comparison.txt

💡 Track which model is "best":
   • Note the Run ID
   • Add it to your deployment README
   • Reference it in production

💡 Version control your models:
   • Save best model path
   • Document score and metrics
   • Keep old versions for rollback


═══════════════════════════════════════════════════════════════════════════════

🎯 REMEMBER: Your best model is now at models/model.joblib
              Ready for deployment and predictions!

═══════════════════════════════════════════════════════════════════════════════

For questions or issues: See docs/06-troubleshooting.md or inspect MLflow logs

Last Updated: 2025-01-01
Tool Version: 1.0
Status: ✅ Production Ready

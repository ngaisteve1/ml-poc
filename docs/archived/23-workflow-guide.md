#!/usr/bin/env python3
"""
ML POC Integration Guide - What to Run and In What Order

This file shows the complete workflow for your ML POC project.
Use it as a checklist when working with your models.
"""

# ============================================================================
# WORKFLOW 1: Initial Setup (One-Time)
# ============================================================================

"""
Step 1: Install Python dependencies
Run this once at the beginning:

    pip install pandas numpy scikit-learn mlflow matplotlib joblib

Then verify MLflow is running:
    
    mlflow ui --host 127.0.0.1 --port 5000
    
Visit: http://127.0.0.1:5000 in your browser to confirm it loads.
"""

# ============================================================================
# WORKFLOW 2: Generate Training Data
# ============================================================================

"""
Option A: Use mock data (safe, no DB access needed)

    python src/ml/generate_mock_data.py --rows 24 --seed 42
    
This creates: data/training_data.csv
Time: ~2 seconds
Result: 24 months of realistic mock data

To use different amount of data:
    python src/ml/generate_mock_data.py --rows 36  # 36 months
    python src/ml/generate_mock_data.py --rows 48  # 48 months

Option B: Use production data (when ready)

    1. Run Query 10 from: setup/02-data-extraction.sql
    2. Export results as CSV to: data/training_data.csv
    3. Keep same column names and format as mock data
    4. Proceed with training
"""

# ============================================================================
# WORKFLOW 3: Train Models (Run Once or Multiple Times)
# ============================================================================

"""
Train a single model and log to MLflow:

    python src/ml/train_with_mlflow.py
    
This:
    ✅ Loads data from: data/training_data.csv
    ✅ Splits into train/test
    ✅ Trains RandomForest model
    ✅ Logs metrics to MLflow
    ✅ Saves model to: models/model.joblib
    ✅ Saves feature importance plot to: MLflow artifacts
    
Time: ~3 seconds
Result: New run appears in MLflow UI

To train multiple models (create variety):

    # Train model 1 (default parameters)
    python src/ml/train_with_mlflow.py
    
    # Train model 2 (generates different random seed, slightly different performance)
    python src/ml/train_with_mlflow.py
    
    # Train model 3 (generates another variation)
    python src/ml/train_with_mlflow.py
    
    # Train model 4 (variations continue)
    python src/ml/train_with_mlflow.py
    
Now you have 4 different models to compare!
"""

# ============================================================================
# WORKFLOW 4: Compare Models (The Most Useful Part!)
# ============================================================================

"""
After training multiple models, compare them automatically:

    python src/ml/compare_models.py

This:
    ✅ Fetches all trained models from MLflow
    ✅ Calculates quality scores (1-23 points)
    ✅ Ranks models from best to worst
    ✅ Shows best model details
    ✅ Provides recommendations
    ✅ Identifies overfitting issues
    
Time: ~2 seconds
Result: Console table showing:
    - Ranking (1st best, 2nd best, etc)
    - Test R² (explains how much variance)
    - Test MAE (prediction error)
    - Overfitting (train vs test gap)
    - Total score (higher = better)

Example output:
    
    Rank  Run ID      Test R²  Test MAE  Score
    ─────────────────────────────────────────────
    1     abc123      0.8543   5.21 GB   23/23 ⭐ BEST
    2     def456      0.7541   6.06 GB   19/23
    3     ghi789      0.7200   8.50 GB   15/23

OPTIONS:
    
    # View top 3 models
    python src/ml/compare_models.py --top 3
    
    # Use different experiment
    python src/ml/compare_models.py --experiment-name "my-experiment"
    
    # Connect to different MLflow server
    python src/ml/compare_models.py --mlflow-uri "http://other-server:5000"
"""

# ============================================================================
# WORKFLOW 5: Understanding the Results
# ============================================================================

"""
After running compare_models.py, you'll see scores like:

    Model A: 23/23 ⭐⭐⭐⭐⭐ EXCELLENT
    Model B: 19/23 ⭐⭐⭐⭐ GOOD
    Model C: 12/23 ⭐⭐ POOR

What do these scores mean?

    Metric               Points   How It's Calculated
    ─────────────────────────────────────────────────
    Test R²                5     Higher R² = more points
    Test MAE               5     Lower MAE (GB) = more points
    Test RMSE              5     Lower RMSE (GB) = more points
    Overfitting            5     Smaller train/test gap = more points
    Speed                  3     Faster training = more points
    ─────────────────────────────────────────────────
    TOTAL               23/23

Interpretation:

    20-23: ⭐⭐⭐⭐⭐ Excellent - Production ready, use immediately
    17-19: ⭐⭐⭐⭐ Good - Production ready with monitoring
    14-16: ⭐⭐⭐ Acceptable - Works but needs improvement
    11-13: ⭐⭐ Poor - Needs significant work
     0-10: ⭐ Very Poor - Not recommended

Your Decision:
    → Pick the model with HIGHEST SCORE
    → Usually correlates with best test metrics
    → Automatically detects overfitting issues
"""

# ============================================================================
# WORKFLOW 6: Deploy Best Model
# ============================================================================

"""
Once you've chosen the best model, use it for predictions:

    import joblib
    
    # Load the trained model
    model = joblib.load('models/model.joblib')
    
    # Make predictions on new data
    predictions = model.predict(your_new_data)
    
    # Predictions are: [files_archived, volume_gb] for each input row

The model is ready for:
    ✅ API endpoints
    ✅ Batch predictions
    ✅ Reports and dashboards
    ✅ Forecasting tools
    ✅ Production deployment
"""

# ============================================================================
# WORKFLOW 7: Monthly Retraining
# ============================================================================

"""
Every month, generate new data and retrain:

    Step 1: Get latest data
    ─────────────────────────
    python src/ml/generate_mock_data.py --rows 36 --seed <new_seed>
    # Or: Run Query 10 from SQL Server and export to data/training_data.csv
    
    Step 2: Train new models
    ────────────────────────
    python src/ml/train_with_mlflow.py
    python src/ml/train_with_mlflow.py  # Train multiple variations
    
    Step 3: Compare new models
    ──────────────────────────
    python src/ml/compare_models.py
    
    Step 4: Check if new model is better
    ────────────────────────────────────
    # If new best > current production model score:
    #   → Update production model
    #   → Update model_id in your application
    #   → Log the change in your deployment notes
    # 
    # If new best ≤ current production model score:
    #   → Keep current model in production
    #   → Archive new model for reference
    #   → Try different hyperparameters next time

This ensures your model stays current with latest data trends.
"""

# ============================================================================
# QUICK REFERENCE: All Commands
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                        COMMAND QUICK REFERENCE                            ║
╚════════════════════════════════════════════════════════════════════════════╝

Generate Data:
──────────────
  python src/ml/generate_mock_data.py
  python src/ml/generate_mock_data.py --rows 36
  python src/ml/generate_mock_data.py --rows 48 --seed 999

Train Models:
─────────────
  python src/ml/train_with_mlflow.py

Compare Models (MOST USEFUL):
─────────────────────────────
  python src/ml/compare_models.py
  python src/ml/compare_models.py --top 3
  python src/ml/compare_models.py --experiment-name "my-exp"

View Results:
─────────────
  Open: http://127.0.0.1:5000
  Or run: mlflow ui --host 127.0.0.1 --port 5000

Load Model for Predictions:
───────────────────────────
  python
  >>> import joblib
  >>> model = joblib.load('models/model.joblib')
  >>> predictions = model.predict(X_new)
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
Problem 1: "No runs found in experiment"
─────────────────────────────────────────
Cause: Haven't trained any models yet
Solution:
    1. Train a model: python src/ml/train_with_mlflow.py
    2. Then compare: python src/ml/compare_models.py

Problem 2: "Connection refused" to MLflow
──────────────────────────────────────────
Cause: MLflow not running
Solution:
    1. Start MLflow: mlflow ui --host 127.0.0.1 --port 5000
    2. In separate terminal: python src/ml/compare_models.py

Problem 3: "No completed runs with metrics found"
──────────────────────────────────────────────────
Cause: MLflow data missing or experiment name wrong
Solution:
    1. Check MLflow UI: http://127.0.0.1:5000
    2. Find experiment name (usually "Archive-Forecast-ML-POC")
    3. Run: python src/ml/compare_models.py --experiment-name "actual-name"

Problem 4: "Error loading data/training_data.csv"
─────────────────────────────────────────────────
Cause: File doesn't exist or wrong format
Solution:
    1. Generate data: python src/ml/generate_mock_data.py
    2. Verify file exists: data/training_data.csv
    3. Check has 13 columns and headers

Problem 5: "Model score seems low (< 15/23)"
─────────────────────────────────────────────
Cause: Small dataset or model needs tuning
Solution:
    1. Use more data: python src/ml/generate_mock_data.py --rows 48
    2. Train again: python src/ml/train_with_mlflow.py
    3. Or: Try different hyperparameters in train_with_mlflow.py

See docs/06-troubleshooting.md for more help.
"""

# ============================================================================
# FILE LOCATIONS QUICK REFERENCE
# ============================================================================

"""
When you need to...                           Look in this file
─────────────────────────────────────────────────────────────────────
Generate mock data                            src/ml/generate_mock_data.py
Train ML model                                src/ml/train_with_mlflow.py
Compare models ⭐ MOST USED                   src/ml/compare_models.py
Preprocess data                               src/ml/data_preprocessing.py
Extract production data                       setup/02-data-extraction.sql
Create database indexes                       setup/01-create-indexes.sql

Understand how comparison scoring works       docs/14-model-comparison-tool.md
Manual decision framework                     docs/13-model-selection.md
MLflow setup instructions                     docs/08-mlflow-integration.md
Complete workflow guide                       docs/09-complete-workflow.md
Troubleshooting & support                     docs/06-troubleshooting.md

Quick reference for all commands              COMPARE_MODELS_COMMANDS.txt
Overall project summary                       COMPLETE_SETUP_SUMMARY.md
This integration guide                        WORKFLOW_GUIDE.md (this file)
"""

# ============================================================================
# SUCCESS CHECKLIST
# ============================================================================

"""
✅ Completed Setup:
    ☐ Python installed (pip install pandas numpy scikit-learn mlflow)
    ☐ MLflow running (mlflow ui --host 127.0.0.1 --port 5000)
    ☐ Mock data generated (python src/ml/generate_mock_data.py)
    ☐ Model trained (python src/ml/train_with_mlflow.py)
    ☐ Run compare tool (python src/ml/compare_models.py)

✅ Ready for Production:
    ☐ Best model identified
    ☐ Model score > 15/23
    ☐ Overfitting < 0.25 (good generalization)
    ☐ Test R² > 0.70
    ☐ Model exported (models/model.joblib)

✅ Documentation:
    ☐ Understand scoring system (docs/14-model-comparison-tool.md)
    ☐ Know your model metrics
    ☐ Can explain why one model beat another
    ☐ Have deployment plan for best model
"""

# ============================================================================
# NEXT STEPS
# ============================================================================

"""
🚀 Your Next Action (Right Now):

    1. Make sure MLflow is running:
       mlflow ui --host 127.0.0.1 --port 5000
    
    2. Generate training data:
       python src/ml/generate_mock_data.py --rows 24
    
    3. Train first model:
       python src/ml/train_with_mlflow.py
    
    4. Train second model:
       python src/ml/train_with_mlflow.py
    
    5. Compare models:
       python src/ml/compare_models.py
    
    6. View results:
       Check output to see which model won

Total time: ~10 seconds! ⚡

That's it! You now have your first ML comparison working.
"""

print(__doc__)

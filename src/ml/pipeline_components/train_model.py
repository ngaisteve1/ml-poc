"""
SmartArchive Model Training Component
Trains RandomForest model to predict archive volume and storage savings.
Uses MultiOutputRegressor to predict two targets:
  1. archived_gb_next_period
  2. savings_gb_next_period
"""
import os
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import pandas as pd
import numpy as np
import argparse
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer features for the archive forecasting model.
    Includes cyclical encoding for months, file type compositions, etc.
    """
    df = df.copy()
    
    # Parse month if needed
    if 'month' in df.columns and isinstance(df['month'].iloc[0], str):
        months = pd.to_datetime(df['month']).dt.month
    elif 'date' in df.columns:
        months = pd.to_datetime(df['date']).dt.month
    else:
        months = np.ones(len(df))
    
    # Cyclical encoding for month
    df['month_sin'] = np.sin(2 * np.pi * months / 12)
    df['month_cos'] = np.cos(2 * np.pi * months / 12)
    
    # Ensure percentage columns sum to ~1
    if 'pct_other' not in df.columns:
        df['pct_other'] = 1.0 - (df.get('pct_pdf', 0) + df.get('pct_docx', 0) + df.get('pct_xlsx', 0))
        df['pct_other'] = df['pct_other'].clip(lower=0.0)
    
    # Select feature columns
    feature_cols = [
        'total_files', 'avg_file_size_mb', 'pct_pdf', 'pct_docx', 'pct_xlsx', 'pct_other',
        'archive_frequency_per_day', 'month_sin', 'month_cos'
    ]
    
    # Keep only existing columns
    feature_cols = [col for col in feature_cols if col in df.columns]
    
    return df[feature_cols]

def train_archive_model(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    n_estimators: int = 100
) -> dict:
    """
    Train RandomForest model with MultiOutputRegressor for archive forecasting.
    Returns model and metrics.
    """
    
    logger.info(f"Training RandomForestRegressor with {n_estimators} estimators...")
    logger.info(f"Training data shape: X={X_train.shape}, y={y_train.shape}")
    
    # Create MultiOutputRegressor with RandomForest
    model = MultiOutputRegressor(
        RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=42,
            n_jobs=-1,
            max_depth=10
        )
    )
    
    # Train model
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics for each output
    mae_output1 = mean_absolute_error(y_test[:, 0], y_pred[:, 0])
    mae_output2 = mean_absolute_error(y_test[:, 1], y_pred[:, 1])
    rmse_output1 = np.sqrt(mean_squared_error(y_test[:, 0], y_pred[:, 0]))
    rmse_output2 = np.sqrt(mean_squared_error(y_test[:, 1], y_pred[:, 1]))
    r2_output1 = r2_score(y_test[:, 0], y_pred[:, 0])
    r2_output2 = r2_score(y_test[:, 1], y_pred[:, 1])
    
    # Average metrics
    mae = (mae_output1 + mae_output2) / 2
    rmse = (rmse_output1 + rmse_output2) / 2
    r2 = (r2_output1 + r2_output2) / 2
    
    logger.info(f"Model trained successfully!")
    logger.info(f"  Archived GB - MAE: {mae_output1:.4f}, RMSE: {rmse_output1:.4f}, R²: {r2_output1:.4f}")
    logger.info(f"  Savings GB  - MAE: {mae_output2:.4f}, RMSE: {rmse_output2:.4f}, R²: {r2_output2:.4f}")
    logger.info(f"  Average     - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")
    
    return {
        'model': model,
        'y_pred': y_pred,
        'metrics': {
            'mae': float(mae),
            'rmse': float(rmse),
            'r2': float(r2),
            'mae_archived_gb': float(mae_output1),
            'rmse_archived_gb': float(rmse_output1),
            'r2_archived_gb': float(r2_output1),
            'mae_savings_gb': float(mae_output2),
            'rmse_savings_gb': float(rmse_output2),
            'r2_savings_gb': float(r2_output2),
            'n_estimators': n_estimators
        }
    }

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Train SmartArchive archive forecasting model"
    )
    parser.add_argument("--input_data", type=str, required=True, help="Input prepared data directory or CSV file")
    parser.add_argument("--n_estimators", type=int, default=100, help="Number of trees in RandomForest")
    parser.add_argument("--output_model", type=str, required=True, help="Output directory for trained model")
    parser.add_argument(
        "--metrics_output",
        type=str,
        default=None,
        help="Output file for metrics (default: <output_model>/metrics.json)"
    )
    args = parser.parse_args()
    
    # Set default metrics output if not provided
    if args.metrics_output is None:
        args.metrics_output = os.path.join(args.output_model, 'metrics.json')
    
    print("=" * 60)
    print("SmartArchive Model Training Component")
    print("=" * 60)
    
    # Load prepared data
    # Handle both cases: direct CSV file or directory with archive-data.csv
    if args.input_data.endswith('.csv'):
        input_file = args.input_data
    else:
        input_file = os.path.join(args.input_data, "archive-data.csv")
    
    logger.info(f"Loading data from: {input_file}")
    
    if not os.path.exists(input_file):
        logger.error(f"ERROR: File not found: {input_file}")
        logger.error(f"Check input path: {args.input_data}")
        if os.path.exists(args.input_data):
            logger.error(f"Contents of {args.input_data}: {os.listdir(args.input_data)}")
        exit(1)
    
    df = pd.read_csv(input_file)
    logger.info(f"Data loaded. Shape: {df.shape}")
    
    # Prepare features and targets
    X = build_features(df)
    logger.info(f"Features engineered. Shape: {X.shape}")
    logger.info(f"Features: {X.columns.tolist()}")
    
    # Targets: archive volume and savings
    if 'archived_gb' not in df.columns or 'savings_gb' not in df.columns:
        logger.error("ERROR: Missing 'archived_gb' or 'savings_gb' columns")
        exit(1)
    
    y = df[['archived_gb', 'savings_gb']].values
    logger.info(f"Targets shape: {y.shape}")
    
    # Convert to numeric and handle NaN
    X = X.apply(pd.to_numeric, errors='coerce')
    mask = X.notnull().all(axis=1) & (y != np.nan).all(axis=1)
    X = X[mask].values
    y = y[mask]
    
    logger.info(f"Data after cleaning: X shape={X.shape}, y shape={y.shape}")
    if X.shape[0] == 0:
        logger.error("ERROR: No valid data after cleaning")
        exit(1)
    
    # Scale features
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    logger.info("Features scaled with StandardScaler")
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    logger.info(f"Train/test split: {X_train.shape[0]} train, {X_test.shape[0]} test")
    
    # Train model
    training_results = train_archive_model(
        X_train, X_test, y_train, y_test,
        n_estimators=args.n_estimators
    )
    
    model = training_results['model']
    metrics = training_results['metrics']
    
    # Log to MLflow (optional - skip if experiment not found)
    try:
        # Set or create experiment
        experiment_name = "SmartArchive_Training"
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
        else:
            experiment_id = experiment.experiment_id
        
        with mlflow.start_run(experiment_id=experiment_id):
            mlflow.log_param("n_estimators", args.n_estimators)
            mlflow.log_param("model_type", "RandomForest + MultiOutput")
            mlflow.log_param("train_size", X_train.shape[0])
            mlflow.log_param("test_size", X_test.shape[0])
            
            for metric_name, metric_value in metrics.items():
                if metric_name != 'n_estimators':
                    mlflow.log_metric(metric_name, metric_value)
        
        logger.info("Metrics logged to MLflow")
    except Exception as e:
        logger.warning(f"Could not log to MLflow: {e}. Continuing without MLflow logging.")
    
    # Create output directory for model (parent directory only)
    output_parent = os.path.dirname(args.output_model)
    if output_parent:
        os.makedirs(output_parent, exist_ok=True)
    
    # Save model (mlflow will create the output_model directory)
    mlflow.sklearn.save_model(model, args.output_model)
    logger.info(f"✅ Model saved to: {args.output_model}")
    
    # Save metrics
    metrics_file = args.metrics_output
    metrics_dir = os.path.dirname(metrics_file)
    if metrics_dir:
        os.makedirs(metrics_dir, exist_ok=True)
    
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"✅ Metrics saved to: {metrics_file}")
    
    print("\n" + "=" * 60)
    print("Model Training Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

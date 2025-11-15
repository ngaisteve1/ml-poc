"""
Compare Models from MLflow Experiment

This script helps you determine which model is best by:
1. Fetching all runs from an experiment
2. Calculating comparison scores
3. Identifying the best model
4. Showing detailed analysis

Usage:
    python src/ml/compare_models.py
    python src/ml/compare_models.py --experiment-name "my-experiment"
    python src/ml/compare_models.py --top 3
"""

import argparse
import pandas as pd
from pathlib import Path
import mlflow
import json


def setup_mlflow(mlflow_uri: str = "http://127.0.0.1:5000"):
    """Setup MLflow connection."""
    mlflow.set_tracking_uri(mlflow_uri)
    print(f"✅ Connected to MLflow: {mlflow_uri}")


def get_experiment(experiment_name: str = "Archive-Forecast-ML-POC"):
    """Get experiment by name."""
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            print(f"❌ Experiment '{experiment_name}' not found")
            return None
        return experiment
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def fetch_runs(experiment_id: str):
    """Fetch all completed runs from experiment."""
    client = mlflow.MlflowClient()
    runs = client.search_runs(
        experiment_ids=[experiment_id],
        order_by=["start_time DESC"],
        max_results=100
    )
    print(f"✅ Found {len(runs)} runs")
    return runs


def extract_metrics(run):
    """Extract key metrics from run."""
    metrics = run.data.metrics
    return {
        'run_id': run.info.run_id[:8],  # Short ID
        'run_name': run.info.run_name or 'unnamed',
        'test_r2': metrics.get('test_r2', None),
        'test_mae': metrics.get('test_mae', None),
        'test_rmse': metrics.get('test_rmse', None),
        'train_r2': metrics.get('train_r2', None),
        'train_mae': metrics.get('train_mae', None),
        'full_run_id': run.info.run_id,
        'duration_sec': (run.info.end_time - run.info.start_time) / 1000 if run.info.end_time else None
    }


def calculate_score(metrics: dict) -> tuple:
    """
    Calculate model score (1-5 for each metric).
    Returns: (total_score, max_score, breakdown)
    """
    breakdown = {}
    total_score = 0
    max_possible = 0
    
    # Test R² score (max 5 points)
    if metrics['test_r2'] is not None:
        r2 = metrics['test_r2']
        if r2 > 0.80:
            breakdown['test_r2_score'] = 5
        elif r2 > 0.75:
            breakdown['test_r2_score'] = 4
        elif r2 > 0.70:
            breakdown['test_r2_score'] = 3
        elif r2 > 0.60:
            breakdown['test_r2_score'] = 2
        else:
            breakdown['test_r2_score'] = 1
        total_score += breakdown['test_r2_score']
    max_possible += 5
    
    # Test MAE score (max 5 points, lower is better)
    if metrics['test_mae'] is not None:
        mae = metrics['test_mae']
        if mae < 5:
            breakdown['test_mae_score'] = 5
        elif mae < 8:
            breakdown['test_mae_score'] = 4
        elif mae < 10:
            breakdown['test_mae_score'] = 3
        elif mae < 15:
            breakdown['test_mae_score'] = 2
        else:
            breakdown['test_mae_score'] = 1
        total_score += breakdown['test_mae_score']
    max_possible += 5
    
    # Test RMSE score (max 5 points, lower is better)
    if metrics['test_rmse'] is not None:
        rmse = metrics['test_rmse']
        if rmse < 8:
            breakdown['test_rmse_score'] = 5
        elif rmse < 10:
            breakdown['test_rmse_score'] = 4
        elif rmse < 12:
            breakdown['test_rmse_score'] = 3
        elif rmse < 15:
            breakdown['test_rmse_score'] = 2
        else:
            breakdown['test_rmse_score'] = 1
        total_score += breakdown['test_rmse_score']
    max_possible += 5
    
    # Overfitting score (max 5 points)
    if metrics['train_r2'] and metrics['test_r2']:
        gap = metrics['train_r2'] - metrics['test_r2']
        if gap < 0.10:
            breakdown['overfit_score'] = 5
        elif gap < 0.15:
            breakdown['overfit_score'] = 4
        elif gap < 0.20:
            breakdown['overfit_score'] = 3
        elif gap < 0.30:
            breakdown['overfit_score'] = 2
        else:
            breakdown['overfit_score'] = 1
        total_score += breakdown['overfit_score']
    max_possible += 5
    
    # Training time score (max 3 points, faster is better)
    if metrics['duration_sec'] is not None:
        duration = metrics['duration_sec']
        if duration < 5:
            breakdown['speed_score'] = 3
        elif duration < 10:
            breakdown['speed_score'] = 2
        else:
            breakdown['speed_score'] = 1
        total_score += breakdown['speed_score']
    max_possible += 3
    
    return total_score, max_possible, breakdown


def display_comparison(runs_data: list):
    """Display comparison table."""
    if not runs_data:
        print("❌ No runs to compare")
        return
    
    print("\n" + "="*100)
    print("MODEL COMPARISON RESULTS")
    print("="*100)
    
    # Create DataFrame
    df = pd.DataFrame(runs_data)
    
    # Sort by score descending
    df = df.sort_values('score', ascending=False)
    
    # Display table
    print("\nRanking:")
    print("-" * 100)
    print(f"{'Rank':<5} {'Run ID':<10} {'Test R²':<10} {'Test MAE':<12} {'Test RMSE':<12} {'Overfit':<10} {'Score':<12}")
    print("-" * 100)
    
    for idx, row in df.iterrows():
        rank = list(df.index).index(idx) + 1
        
        # Format metrics
        r2_str = f"{row['test_r2']:.4f}" if row['test_r2'] else "N/A"
        mae_str = f"{row['test_mae']:.2f} GB" if row['test_mae'] else "N/A"
        rmse_str = f"{row['test_rmse']:.2f} GB" if row['test_rmse'] else "N/A"
        overfit_str = f"{row['overfitting']:.4f}" if row['overfitting'] is not None else "N/A"
        score_str = f"{row['score']:.0f}/{row['max_score']:.0f}"
        
        # Stars
        stars = "⭐" * int(row['score'] / 5)
        
        print(f"{rank:<5} {row['run_id']:<10} {r2_str:<10} {mae_str:<12} {rmse_str:<12} {overfit_str:<10} {score_str:<12} {stars}")
    
    print("-" * 100)


def show_best_model(best_run: dict):
    """Display best model details."""
    print("\n" + "="*100)
    print("🏆 BEST MODEL")
    print("="*100)
    
    print(f"\nRun ID: {best_run['full_run_id']}")
    print(f"Run Name: {best_run['run_name']}")
    print(f"\nMetrics:")
    print(f"  Test R²:   {best_run['test_r2']:.4f} {'✅' if best_run['test_r2'] > 0.75 else '⚠️'}")
    print(f"  Test MAE:  {best_run['test_mae']:.2f} GB {'✅' if best_run['test_mae'] < 10 else '⚠️'}")
    print(f"  Test RMSE: {best_run['test_rmse']:.2f} GB")
    print(f"  Train R²:  {best_run['train_r2']:.4f}")
    print(f"  Train MAE: {best_run['train_mae']:.2f} GB")
    print(f"\nOverfitting:")
    print(f"  R² Gap: {best_run['train_r2'] - best_run['test_r2']:.4f} {'✅' if (best_run['train_r2'] - best_run['test_r2']) < 0.20 else '⚠️'}")
    print(f"  MAE Ratio: {best_run['train_mae'] / best_run['test_mae']:.2f}x {'✅' if (best_run['train_mae'] / best_run['test_mae']) < 5 else '⚠️'}")
    print(f"\nTraining Time: {best_run['duration_sec']:.1f} seconds")
    print(f"Score: {best_run['score']:.0f}/{best_run['max_score']:.0f} ⭐" * int(best_run['score'] / 5))
    
    print("\n" + "="*100)


def show_recommendations(best_run: dict):
    """Show recommendations based on best model."""
    print("\n📋 RECOMMENDATIONS:")
    print("-" * 100)
    
    recommendations = []
    
    # Check Test R²
    if best_run['test_r2'] < 0.75:
        recommendations.append("⚠️  Test R² is low. Consider: more features, more data, or different algorithms")
    elif best_run['test_r2'] > 0.85:
        recommendations.append("✅ Test R² is excellent. Model is ready for use.")
    else:
        recommendations.append("✅ Test R² is good. Model is production-ready.")
    
    # Check Test MAE
    if best_run['test_mae'] > 15:
        recommendations.append("⚠️  Test MAE is high. Consider: improving features or data quality")
    else:
        recommendations.append(f"✅ Test MAE ({best_run['test_mae']:.2f} GB) is acceptable.")
    
    # Check Overfitting
    gap = best_run['train_r2'] - best_run['test_r2']
    if gap > 0.30:
        recommendations.append("⚠️  High overfitting detected. Try: regularization, more data, or simpler model")
    elif gap > 0.20:
        recommendations.append("⚠️  Some overfitting detected. Monitor carefully in production")
    else:
        recommendations.append("✅ Overfitting is minimal. Good generalization expected.")
    
    # Next Steps
    recommendations.append("\n📌 Next Steps:")
    recommendations.append(f"   1. Model ready at: models/model.joblib")
    recommendations.append(f"   2. Use in API or batch predictions")
    recommendations.append(f"   3. Validate with production data (when ready)")
    recommendations.append(f"   4. Set up monthly retraining with new data")
    
    for rec in recommendations:
        print(rec)
    
    print("-" * 100)


def main():
    parser = argparse.ArgumentParser(description="Compare models from MLflow experiment")
    parser.add_argument(
        "--experiment-name",
        default="Archive-Forecast-ML-POC",
        help="MLflow experiment name (default: Archive-Forecast-ML-POC)"
    )
    parser.add_argument(
        "--mlflow-uri",
        default="http://127.0.0.1:5000",
        help="MLflow tracking URI (default: http://127.0.0.1:5000)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="Show only top N models (default: all)"
    )
    
    args = parser.parse_args()
    
    try:
        print("🔍 Comparing Models in MLflow...\n")
        
        # Setup
        setup_mlflow(args.mlflow_uri)
        
        # Get experiment
        experiment = get_experiment(args.experiment_name)
        if not experiment:
            return
        
        # Fetch runs
        runs = fetch_runs(experiment.experiment_id)
        if not runs:
            print("❌ No runs found")
            return
        
        # Process runs
        runs_data = []
        for run in runs:
            metrics = extract_metrics(run)
            if metrics['test_r2'] is not None:  # Only include completed runs
                score, max_score, breakdown = calculate_score(metrics)
                metrics['score'] = score
                metrics['max_score'] = max_score
                metrics['breakdown'] = breakdown
                metrics['overfitting'] = metrics['train_r2'] - metrics['test_r2'] if metrics['train_r2'] else None
                runs_data.append(metrics)
        
        if not runs_data:
            print("❌ No completed runs with metrics found")
            return
        
        # Limit to top N
        if args.top:
            runs_data = sorted(runs_data, key=lambda x: x['score'], reverse=True)[:args.top]
        
        # Display comparison
        display_comparison(runs_data)
        
        # Show best model
        best_run = max(runs_data, key=lambda x: x['score'])
        show_best_model(best_run)
        
        # Show recommendations
        show_recommendations(best_run)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()

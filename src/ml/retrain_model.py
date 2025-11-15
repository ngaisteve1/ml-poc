"""
Model Retraining Script

Retrains the anomaly detection model using feedback and recent monitoring data.
Logs metrics to MLflow and updates model registry.
"""

import os
import sys
import json
import mlflow
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.feedback_db import FeedbackDB
from monitoring.predictions_db import PredictionsDB


class ModelRetrainer:
    """Handles model retraining with feedback data"""
    
    def __init__(
        self,
        model_name: str = "smart-archive-anomaly",
        experiment_name: str = "smart-archive-retraining",
        db_path: str = "monitoring.db"
    ):
        """
        Initialize retrainer
        
        Args:
            model_name: Name of model in MLflow registry
            experiment_name: MLflow experiment name
            db_path: Path to monitoring database
        """
        self.model_name = model_name
        self.experiment_name = experiment_name
        self.db_path = db_path
        self.feedback_db = FeedbackDB(db_path)
        self.predictions_db = PredictionsDB(db_path)
        
        # Set up MLflow
        mlflow.set_experiment(experiment_name)
    
    def load_training_data(self, days: int = 90) -> pd.DataFrame:
        """
        Load training data from feedback and predictions
        
        Args:
            days: Number of days of historical data to include
        
        Returns:
            DataFrame with training data
        """
        print(f"[DATA] Loading training data from last {days} days...")
        
        # Get feedback data
        feedback_df = self.feedback_db.get_recent_feedback(days=days)
        
        if feedback_df.empty:
            print("[WARN] No feedback data found - using predictions only")
            # Get recent predictions for training
            predictions_df = self.predictions_db.get_predictions(days=days)
            if predictions_df.empty:
                raise ValueError("No training data available")
            return predictions_df
        
        print(f"[OK] Loaded {len(feedback_df)} feedback records")
        return feedback_df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, pd.Series, pd.DataFrame]:
        """
        Prepare features for training
        
        Args:
            df: Input dataframe
        
        Returns:
            Tuple of (X, y, scaler_df) where:
            - X: Feature matrix (normalized)
            - y: Target values
            - scaler_df: Original dataframe for reference
        """
        print(f"[PREPARE] Preparing features...")
        
        # Create features from available columns
        feature_cols = []
        
        if 'predicted_value' in df.columns and 'actual_value' in df.columns:
            # Use prediction error as features
            df['prediction_error'] = abs(df['actual_value'] - df['predicted_value'])
            df['prediction_error_pct'] = (df['prediction_error'] / (df['actual_value'] + 0.001)) * 100
            feature_cols = ['predicted_value', 'actual_value', 'prediction_error', 'prediction_error_pct']
        elif 'archived_gb_predicted' in df.columns:
            # Use prediction data
            feature_cols = ['archived_gb_predicted']
            if 'archived_gb_actual' in df.columns:
                df['archived_gb_error'] = abs(df['archived_gb_actual'] - df['archived_gb_predicted'])
                feature_cols.append('archived_gb_error')
        else:
            # Create dummy features for demo
            df['value_scaled'] = np.arange(len(df)) / len(df)
            df['noise'] = np.random.randn(len(df))
            feature_cols = ['value_scaled', 'noise']
        
        # Handle missing values
        X = df[feature_cols].fillna(df[feature_cols].mean())
        
        # Normalize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Create target (anomaly flag based on feedback)
        if 'feedback_status' in df.columns:
            y = (df['feedback_status'] == 'incorrect').astype(int)
        else:
            # Default: no anomalies if no feedback
            y = pd.Series(np.zeros(len(df)), index=df.index)
        
        print(f"[OK] Prepared {X_scaled.shape[0]} samples with {X_scaled.shape[1]} features")
        print(f"   Anomalies: {y.sum()} ({y.sum()/len(y)*100:.1f}%)")
        
        return X_scaled, y, df
    
    def train_model(
        self,
        X: np.ndarray,
        y: pd.Series,
        contamination: float = 0.1,
        random_state: int = 42
    ) -> IsolationForest:
        """
        Train isolation forest model
        
        Args:
            X: Feature matrix
            y: Target values (for reference only - isolation forest is unsupervised)
            contamination: Expected anomaly rate
            random_state: Random seed
        
        Returns:
            Trained model
        """
        print(f"[TRAIN] Training Isolation Forest (contamination={contamination})...")
        
        model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
            verbose=0
        )
        
        model.fit(X)
        
        print("[OK] Model training complete")
        return model
    
    def evaluate_model(
        self,
        model: IsolationForest,
        X: np.ndarray,
        y: pd.Series,
        baseline_model: Optional[IsolationForest] = None
    ) -> Dict:
        """
        Evaluate model performance
        
        Args:
            model: Trained model
            X: Feature matrix
            y: True labels (if available)
            baseline_model: Baseline model for comparison
        
        Returns:
            Dictionary with evaluation metrics
        """
        print("[EVAL] Evaluating model...")
        
        # Get anomaly scores
        scores = -model.score_samples(X)  # Negative scores for anomalies
        predictions = model.predict(X)  # -1 for anomalies, 1 for normal
        
        # Calculate metrics
        anomaly_rate = (predictions == -1).sum() / len(predictions)
        mean_score = scores.mean()
        std_score = scores.std()
        
        metrics = {
            'anomaly_rate': anomaly_rate,
            'mean_anomaly_score': mean_score,
            'std_anomaly_score': std_score,
            'n_samples': len(X),
            'n_features': X.shape[1]
        }
        
        # Compare with baseline if available
        if baseline_model is not None:
            baseline_scores = -baseline_model.score_samples(X)
            score_improvement = (baseline_scores.mean() - mean_score) / (baseline_scores.mean() + 0.001)
            metrics['baseline_mean_score'] = baseline_scores.mean()
            metrics['score_improvement'] = score_improvement
            print(f"   Baseline score: {baseline_scores.mean():.4f}")
            print(f"   New score: {mean_score:.4f}")
            print(f"   Improvement: {score_improvement*100:+.2f}%")
        
        print(f"   Anomaly rate: {anomaly_rate*100:.1f}%")
        print(f"   Mean score: {mean_score:.4f}")
        
        return metrics
    
    def log_to_mlflow(
        self,
        model: IsolationForest,
        metrics: Dict,
        params: Dict,
        feedback_count: int,
        drift_score: float
    ) -> str:
        """
        Log model and metrics to MLflow
        
        Args:
            model: Trained model
            metrics: Evaluation metrics
            params: Model parameters
            feedback_count: Number of feedback records used
            drift_score: Drift detection score
        
        Returns:
            Run ID
        """
        print("[MLFLOW] Logging to MLflow...")
        
        with mlflow.start_run() as run:
            # Log parameters
            mlflow.log_params({
                **params,
                'feedback_count': feedback_count,
                'drift_score': drift_score
            })
            
            # Log metrics
            mlflow.log_metrics(metrics)
            
            # Log model
            mlflow.sklearn.log_model(model, "model")
            
            # Log tags
            mlflow.set_tag("stage", "retraining")
            mlflow.set_tag("model_type", "IsolationForest")
            
            run_id = run.info.run_id
            print(f"[OK] Logged run: {run_id}")
            
            return run_id
    
    def retrain(
        self,
        feedback_count: int = 0,
        drift_score: float = 0.0,
        contamination: float = 0.1,
        days: int = 90
    ) -> Dict:
        """
        Execute full retraining pipeline
        
        Args:
            feedback_count: Number of feedback records used
            drift_score: Current drift score
            contamination: Anomaly contamination rate
            days: Days of historical data to use
        
        Returns:
            Dictionary with retraining results
        """
        print("\n" + "="*60)
        print("[RETRAINING] PIPELINE STARTED")
        print("="*60)
        
        try:
            # Step 1: Load data
            df = self.load_training_data(days=days)
            
            # Step 2: Prepare features
            X, y, df_processed = self.prepare_features(df)
            
            # Step 3: Train model
            model = self.train_model(X, y, contamination=contamination)
            
            # Step 4: Evaluate
            params = {'contamination': contamination}
            metrics = self.evaluate_model(model, X, y)
            
            # Step 5: Log to MLflow
            run_id = self.log_to_mlflow(
                model=model,
                metrics=metrics,
                params=params,
                feedback_count=feedback_count,
                drift_score=drift_score
            )
            
            # Step 6: Log retraining completion
            retraining_id = self.feedback_db.log_retraining_start(
                trigger_reason=f"Feedback: {feedback_count}, Drift: {drift_score:.2f}",
                feedback_count=feedback_count,
                drift_score=drift_score,
                accuracy_drop=0.0
            )
            
            metrics_before = {"baseline": "v1.0"}
            metrics_after = json.dumps({k: float(v) if isinstance(v, np.floating) else v 
                                       for k, v in metrics.items()})
            
            self.feedback_db.log_retraining_complete(
                retraining_id=retraining_id,
                model_improvement=metrics.get('score_improvement', 0.0),
                metrics_before=json.dumps(metrics_before),
                metrics_after=metrics_after
            )
            
            # Step 7: Save model to disk
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)
            model_path = model_dir / f"anomaly_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            
            import pickle
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            print(f"[OK] Model saved to: {model_path}")
            
            print("\n" + "="*60)
            print("[OK] RETRAINING PIPELINE COMPLETED")
            print("="*60)
            
            return {
                'status': 'success',
                'run_id': run_id,
                'model_path': str(model_path),
                'metrics': metrics,
                'retraining_id': retraining_id
            }
        
        except Exception as e:
            print(f"\n[ERROR] RETRAINING FAILED: {e}")
            print("="*60)
            return {
                'status': 'failed',
                'error': str(e)
            }
        
        finally:
            self.feedback_db.close()
            self.predictions_db.close()


def main():
    """Main retraining entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Retrain Smart Archive anomaly model')
    parser.add_argument('--feedback-count', type=int, default=120, help='Number of feedback records')
    parser.add_argument('--drift-score', type=float, default=0.0, help='Drift detection score')
    parser.add_argument('--contamination', type=float, default=0.1, help='Anomaly contamination rate')
    parser.add_argument('--days', type=int, default=90, help='Days of historical data')
    
    args = parser.parse_args()
    
    retrainer = ModelRetrainer()
    result = retrainer.retrain(
        feedback_count=args.feedback_count,
        drift_score=args.drift_score,
        contamination=args.contamination,
        days=args.days
    )
    
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")
    
    return 0 if result['status'] == 'success' else 1


if __name__ == '__main__':
    exit(main())

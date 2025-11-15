"""
Predictions Database Module

Handles storage and retrieval of predictions using SQLite.
Schema supports tracking predictions against actual values for drift detection.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple


class PredictionsDB:
    """SQLite database for storing and retrieving predictions"""
    
    def __init__(self, db_path: str = 'predictions.db'):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Create database and tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        
        # Create predictions table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_date DATE NOT NULL,
                archived_gb_predicted REAL NOT NULL,
                savings_gb_predicted REAL NOT NULL,
                archived_gb_actual REAL,
                savings_gb_actual REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(prediction_date)
            )
        ''')
        
        # Create monitoring events table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_severity TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create model metrics table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date DATE NOT NULL,
                r2_score REAL,
                rmse REAL,
                mae REAL,
                mape REAL,
                accuracy REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(metric_date)
            )
        ''')
        
        self.conn.commit()
    
    def save_prediction(
        self,
        prediction_date: str,
        archived_gb_predicted: float,
        savings_gb_predicted: float,
        archived_gb_actual: Optional[float] = None,
        savings_gb_actual: Optional[float] = None
    ) -> int:
        """
        Save a prediction to the database
        
        Args:
            prediction_date: Date of prediction (YYYY-MM-DD format)
            archived_gb_predicted: Predicted archived GB
            savings_gb_predicted: Predicted savings GB
            archived_gb_actual: Actual archived GB (optional, added later)
            savings_gb_actual: Actual savings GB (optional, added later)
        
        Returns:
            ID of inserted prediction
        """
        try:
            cursor = self.conn.execute('''
                INSERT OR REPLACE INTO predictions 
                (prediction_date, archived_gb_predicted, savings_gb_predicted, 
                 archived_gb_actual, savings_gb_actual, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                prediction_date,
                archived_gb_predicted,
                savings_gb_predicted,
                archived_gb_actual,
                savings_gb_actual
            ))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error saving prediction: {e}")
            return -1
    
    def update_actual_value(
        self,
        prediction_date: str,
        archived_gb_actual: Optional[float] = None,
        savings_gb_actual: Optional[float] = None
    ) -> bool:
        """
        Update actual values for a prediction (when real data becomes available)
        
        Args:
            prediction_date: Date of prediction
            archived_gb_actual: Actual archived GB
            savings_gb_actual: Actual savings GB
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            self.conn.execute('''
                UPDATE predictions
                SET archived_gb_actual = COALESCE(?, archived_gb_actual),
                    savings_gb_actual = COALESCE(?, savings_gb_actual),
                    updated_at = CURRENT_TIMESTAMP
                WHERE prediction_date = ?
            ''', (archived_gb_actual, savings_gb_actual, prediction_date))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating actual value: {e}")
            return False
    
    def get_predictions(
        self,
        days: int = 30,
        include_actuals_only: bool = False
    ) -> pd.DataFrame:
        """
        Get predictions from the last N days
        
        Args:
            days: Number of days to retrieve
            include_actuals_only: If True, only return predictions with actual values
        
        Returns:
            DataFrame with predictions
        """
        where_clause = ""
        if include_actuals_only:
            where_clause = "AND archived_gb_actual IS NOT NULL"
        
        query = f'''
            SELECT 
                id,
                prediction_date,
                archived_gb_predicted,
                savings_gb_predicted,
                archived_gb_actual,
                savings_gb_actual,
                created_at
            FROM predictions
            WHERE DATE(created_at) >= DATE('now', '-' || ? || ' days')
            {where_clause}
            ORDER BY prediction_date DESC
        '''
        
        df = pd.read_sql(query, self.conn, params=(days,))
        if not df.empty:
            df['prediction_date'] = pd.to_datetime(df['prediction_date'])
            df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    
    def get_recent_predictions_for_drift(self, window_size: int = 30) -> Tuple[List[float], List[float]]:
        """
        Get recent predictions for drift detection
        
        Args:
            window_size: Number of recent predictions to get
        
        Returns:
            Tuple of (archived_gb_list, savings_gb_list)
        """
        query = '''
            SELECT archived_gb_predicted, savings_gb_predicted
            FROM predictions
            ORDER BY prediction_date DESC
            LIMIT ?
        '''
        
        df = pd.read_sql(query, self.conn, params=(window_size,))
        
        if df.empty:
            return [], []
        
        return df['archived_gb_predicted'].tolist(), df['savings_gb_predicted'].tolist()
    
    def get_latest_prediction(self) -> Optional[Dict]:
        """
        Get the most recent prediction
        
        Returns:
            Dictionary with latest prediction or None
        """
        query = '''
            SELECT 
                prediction_date,
                archived_gb_predicted,
                savings_gb_predicted,
                archived_gb_actual,
                savings_gb_actual,
                created_at
            FROM predictions
            ORDER BY prediction_date DESC
            LIMIT 1
        '''
        
        cursor = self.conn.execute(query)
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def save_monitoring_event(
        self,
        event_type: str,
        event_severity: str,
        message: str,
        metadata: Optional[str] = None
    ) -> int:
        """
        Log a monitoring event (drift detection, alerts, etc.)
        
        Args:
            event_type: Type of event (e.g., 'drift_detected', 'alert')
            event_severity: Severity level ('info', 'warning', 'error', 'critical')
            message: Event message
            metadata: Optional JSON metadata
        
        Returns:
            ID of inserted event
        """
        try:
            cursor = self.conn.execute('''
                INSERT INTO monitoring_events
                (event_type, event_severity, message, metadata)
                VALUES (?, ?, ?, ?)
            ''', (event_type, event_severity, message, metadata))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error saving monitoring event: {e}")
            return -1
    
    def get_monitoring_events(
        self,
        days: int = 7,
        event_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get monitoring events from the last N days
        
        Args:
            days: Number of days to retrieve
            event_type: Filter by event type (optional)
            severity: Filter by severity level (optional)
        
        Returns:
            DataFrame with monitoring events
        """
        where_clause = "WHERE DATE(created_at) >= DATE('now', '-' || ? || ' days')"
        params = [days]
        
        if event_type:
            where_clause += " AND event_type = ?"
            params.append(event_type)
        
        if severity:
            where_clause += " AND event_severity = ?"
            params.append(severity)
        
        query = f'''
            SELECT 
                id,
                event_type,
                event_severity,
                message,
                metadata,
                created_at
            FROM monitoring_events
            {where_clause}
            ORDER BY created_at DESC
        '''
        
        df = pd.read_sql(query, self.conn, params=params)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    
    def save_model_metrics(
        self,
        metric_date: str,
        r2_score: Optional[float] = None,
        rmse: Optional[float] = None,
        mae: Optional[float] = None,
        mape: Optional[float] = None,
        accuracy: Optional[float] = None
    ) -> int:
        """
        Save model performance metrics
        
        Args:
            metric_date: Date of metric (YYYY-MM-DD format)
            r2_score: R² score
            rmse: Root Mean Squared Error
            mae: Mean Absolute Error
            mape: Mean Absolute Percentage Error
            accuracy: Overall accuracy percentage
        
        Returns:
            ID of inserted metric
        """
        try:
            cursor = self.conn.execute('''
                INSERT OR REPLACE INTO model_metrics
                (metric_date, r2_score, rmse, mae, mape, accuracy)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (metric_date, r2_score, rmse, mae, mape, accuracy))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error saving model metrics: {e}")
            return -1
    
    def get_model_metrics(self, days: int = 30) -> pd.DataFrame:
        """
        Get model metrics from the last N days
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            DataFrame with model metrics
        """
        query = '''
            SELECT 
                id,
                metric_date,
                r2_score,
                rmse,
                mae,
                mape,
                accuracy,
                created_at
            FROM model_metrics
            WHERE DATE(created_at) >= DATE('now', '-' || ? || ' days')
            ORDER BY metric_date DESC
        '''
        
        df = pd.read_sql(query, self.conn, params=(days,))
        if not df.empty:
            df['metric_date'] = pd.to_datetime(df['metric_date'])
            df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    
    def get_summary_statistics(self, days: int = 30) -> Dict:
        """
        Get summary statistics about predictions
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with summary statistics
        """
        df = self.get_predictions(days=days)
        
        if df.empty:
            return {
                'total_predictions': 0,
                'predictions_with_actuals': 0,
                'avg_predicted_archived_gb': 0,
                'avg_predicted_savings_gb': 0
            }
        
        return {
            'total_predictions': len(df),
            'predictions_with_actuals': df['archived_gb_actual'].notna().sum(),
            'avg_predicted_archived_gb': df['archived_gb_predicted'].mean(),
            'avg_predicted_savings_gb': df['savings_gb_predicted'].mean(),
            'avg_actual_archived_gb': df['archived_gb_actual'].mean() if df['archived_gb_actual'].notna().any() else None,
            'avg_actual_savings_gb': df['savings_gb_actual'].mean() if df['savings_gb_actual'].notna().any() else None,
            'date_range': f"{df['prediction_date'].min().date()} to {df['prediction_date'].max().date()}"
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


if __name__ == "__main__":
    """Test database functionality"""
    import json
    
    print("Testing PredictionsDB...")
    print("=" * 60)
    
    # Initialize database
    db = PredictionsDB('test_predictions.db')
    
    # Test 1: Save predictions
    print("\n✓ Test 1: Saving predictions...")
    for i in range(5):
        from datetime import datetime, timedelta
        date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
        db.save_prediction(
            prediction_date=date,
            archived_gb_predicted=250 + i * 2,
            savings_gb_predicted=130 + i * 1.5
        )
    print("  Saved 5 predictions")
    
    # Test 2: Retrieve predictions
    print("\n✓ Test 2: Retrieving predictions...")
    predictions = db.get_predictions(days=30)
    print(f"  Retrieved {len(predictions)} predictions")
    print(f"\n  Sample:\n{predictions.head()}")
    
    # Test 3: Get recent predictions for drift
    print("\n✓ Test 3: Getting predictions for drift detection...")
    archived_list, savings_list = db.get_recent_predictions_for_drift(window_size=5)
    print(f"  Archived GB values: {archived_list}")
    print(f"  Savings GB values: {savings_list}")
    
    # Test 4: Get latest prediction
    print("\n✓ Test 4: Getting latest prediction...")
    latest = db.get_latest_prediction()
    print(f"  Latest: {json.dumps(latest, indent=2, default=str)}")
    
    # Test 5: Save monitoring event
    print("\n✓ Test 5: Saving monitoring event...")
    event_id = db.save_monitoring_event(
        event_type='drift_detected',
        event_severity='warning',
        message='Z-score exceeded threshold (2.5 > 2.0)',
        metadata=json.dumps({'z_score': 2.5, 'threshold': 2.0})
    )
    print(f"  Saved event with ID: {event_id}")
    
    # Test 6: Get monitoring events
    print("\n✓ Test 6: Retrieving monitoring events...")
    events = db.get_monitoring_events(days=7)
    print(f"  Retrieved {len(events)} events")
    print(f"\n  Sample:\n{events.head()}")
    
    # Test 7: Save and retrieve metrics
    print("\n✓ Test 7: Saving model metrics...")
    from datetime import datetime
    db.save_model_metrics(
        metric_date=datetime.now().strftime('%Y-%m-%d'),
        r2_score=0.875,
        rmse=12.34,
        mae=8.92,
        mape=5.2,
        accuracy=87.5
    )
    metrics = db.get_model_metrics(days=1)
    print(f"  Saved and retrieved {len(metrics)} metric record(s)")
    
    # Test 8: Summary statistics
    print("\n✓ Test 8: Getting summary statistics...")
    stats = db.get_summary_statistics(days=30)
    print(f"  Summary:\n{json.dumps(stats, indent=2, default=str)}")
    
    # Cleanup
    db.close()
    print("\n" + "=" * 60)
    print("✅ All tests passed!")

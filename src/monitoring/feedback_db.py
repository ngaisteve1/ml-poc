"""
Feedback Database Module

Handles storage and retrieval of user feedback on predictions.
Used for retraining trigger evaluation and model improvement.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict


class FeedbackDB:
    """SQLite database for storing and retrieving user feedback"""
    
    def __init__(self, db_path: str = 'monitoring.db'):
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
        self.conn.row_factory = sqlite3.Row
        
        # Create feedback table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER,
                prediction_date DATE,
                predicted_value REAL,
                actual_value REAL,
                feedback_status TEXT NOT NULL,
                user_feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id)
            )
        ''')
        
        # Create retraining log table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS retraining_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_reason TEXT NOT NULL,
                feedback_count INTEGER,
                drift_score REAL,
                accuracy_drop REAL,
                model_improvement REAL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                metrics_before TEXT,
                metrics_after TEXT
            )
        ''')
        
        self.conn.commit()
    
    def submit_feedback(
        self,
        prediction_id: int,
        prediction_date: str,
        predicted_value: float,
        actual_value: float,
        feedback_status: str,
        user_feedback: Optional[str] = None
    ) -> int:
        """
        Submit feedback on a prediction
        
        Args:
            prediction_id: ID of prediction
            prediction_date: Date of prediction
            predicted_value: The predicted value
            actual_value: The actual value that occurred
            feedback_status: 'correct', 'incorrect', or 'uncertain'
            user_feedback: Optional user comment
        
        Returns:
            ID of inserted feedback record
        """
        try:
            cursor = self.conn.execute('''
                INSERT INTO feedback 
                (prediction_id, prediction_date, predicted_value, actual_value, 
                 feedback_status, user_feedback)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                prediction_id,
                prediction_date,
                predicted_value,
                actual_value,
                feedback_status,
                user_feedback
            ))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error submitting feedback: {e}")
            return -1
    
    def get_feedback_count(self, days: int = 7) -> int:
        """
        Get count of feedback submitted in last N days
        
        Args:
            days: Number of days to look back
        
        Returns:
            Count of feedback records
        """
        query = '''
            SELECT COUNT(*) as count
            FROM feedback
            WHERE DATE(created_at) >= DATE('now', '-' || ? || ' days')
        '''
        
        cursor = self.conn.execute(query, (days,))
        result = cursor.fetchone()
        return result['count'] if result else 0
    
    def get_recent_feedback(self, days: int = 30, limit: int = 50) -> pd.DataFrame:
        """
        Get recent feedback submissions
        
        Args:
            days: Number of days to look back
            limit: Maximum number of records to return
        
        Returns:
            DataFrame with feedback records
        """
        query = '''
            SELECT 
                id,
                prediction_id,
                prediction_date,
                predicted_value,
                actual_value,
                feedback_status,
                user_feedback,
                created_at
            FROM feedback
            WHERE DATE(created_at) >= DATE('now', '-' || ? || ' days')
            ORDER BY created_at DESC
            LIMIT ?
        '''
        
        df = pd.read_sql(query, self.conn, params=(days, limit))
        if not df.empty:
            df['prediction_date'] = pd.to_datetime(df['prediction_date'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['error'] = abs(df['actual_value'] - df['predicted_value'])
        return df
    
    def get_feedback_accuracy(self, days: int = 30) -> Dict:
        """
        Calculate accuracy metrics from feedback
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with accuracy metrics
        """
        query = '''
            SELECT 
                feedback_status,
                COUNT(*) as count,
                AVG(ABS(actual_value - predicted_value)) as avg_error
            FROM feedback
            WHERE DATE(created_at) >= DATE('now', '-' || ? || ' days')
            GROUP BY feedback_status
        '''
        
        df = pd.read_sql(query, self.conn, params=(days,))
        
        if df.empty:
            return {
                'total_feedback': 0,
                'correct_feedback': 0,
                'incorrect_feedback': 0,
                'uncertain_feedback': 0,
                'accuracy': 0.0,
                'avg_error': 0.0
            }
        
        total = df['count'].sum()
        correct = df[df['feedback_status'] == 'correct']['count'].sum()
        incorrect = df[df['feedback_status'] == 'incorrect']['count'].sum()
        uncertain = df[df['feedback_status'] == 'uncertain']['count'].sum()
        
        avg_error = df['avg_error'].mean() if not df.empty else 0.0
        accuracy = (correct / total * 100) if total > 0 else 0.0
        
        return {
            'total_feedback': int(total),
            'correct_feedback': int(correct),
            'incorrect_feedback': int(incorrect),
            'uncertain_feedback': int(uncertain),
            'accuracy': accuracy,
            'avg_error': avg_error
        }
    
    def log_retraining_start(
        self,
        trigger_reason: str,
        feedback_count: int,
        drift_score: float,
        accuracy_drop: float
    ) -> int:
        """
        Log the start of a retraining session
        
        Args:
            trigger_reason: Reason for triggering retraining
            feedback_count: Number of feedback records used
            drift_score: Drift detection score
            accuracy_drop: Accuracy drop percentage
        
        Returns:
            ID of retraining log record
        """
        try:
            cursor = self.conn.execute('''
                INSERT INTO retraining_log 
                (trigger_reason, feedback_count, drift_score, accuracy_drop, status)
                VALUES (?, ?, ?, ?, 'pending')
            ''', (trigger_reason, feedback_count, drift_score, accuracy_drop))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error logging retraining: {e}")
            return -1
    
    def log_retraining_complete(
        self,
        retraining_id: int,
        model_improvement: float,
        metrics_before: str,
        metrics_after: str
    ) -> bool:
        """
        Log completion of retraining
        
        Args:
            retraining_id: ID of retraining log record
            model_improvement: Improvement percentage
            metrics_before: JSON string of metrics before retraining
            metrics_after: JSON string of metrics after retraining
        
        Returns:
            True if successful
        """
        try:
            self.conn.execute('''
                UPDATE retraining_log
                SET status = 'completed',
                    completed_at = CURRENT_TIMESTAMP,
                    model_improvement = ?,
                    metrics_before = ?,
                    metrics_after = ?
                WHERE id = ?
            ''', (model_improvement, metrics_before, metrics_after, retraining_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating retraining log: {e}")
            return False
    
    def get_retraining_history(self, limit: int = 20) -> pd.DataFrame:
        """
        Get retraining history
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            DataFrame with retraining history
        """
        query = '''
            SELECT 
                id,
                trigger_reason,
                feedback_count,
                drift_score,
                accuracy_drop,
                model_improvement,
                status,
                started_at,
                completed_at
            FROM retraining_log
            ORDER BY started_at DESC
            LIMIT ?
        '''
        
        df = pd.read_sql(query, self.conn, params=(limit,))
        if not df.empty:
            df['started_at'] = pd.to_datetime(df['started_at'])
            df['completed_at'] = pd.to_datetime(df['completed_at'])
        return df
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

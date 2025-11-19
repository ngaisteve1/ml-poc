"""
Cloud-Compatible Feedback Database Module

Handles storage and retrieval of user feedback on predictions.
Supports both local SQLite and cloud-based databases (Azure SQL, PostgreSQL).
Includes Streamlit Cloud persistence using @st.cache_resource.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
import json
from pathlib import Path


class FeedbackDB:
    """Multi-backend feedback database supporting SQLite and cloud databases"""
    
    def __init__(self, db_path: str = 'monitoring.db', use_cloud: bool = False, cloud_config: Optional[Dict] = None):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file (for local mode)
            use_cloud: Whether to use cloud database (Azure SQL, PostgreSQL, etc.)
            cloud_config: Configuration dict with cloud database connection details
                         Format: {
                             'provider': 'azure' | 'postgres',
                             'host': 'server.database.windows.net',
                             'user': 'username',
                             'password': 'password',
                             'database': 'dbname'
                         }
        """
        self.db_path = db_path
        self.use_cloud = use_cloud
        self.cloud_config = cloud_config or {}
        self.conn = None
        self.provider = cloud_config.get('provider', 'sqlite') if use_cloud else 'sqlite'
        
        # Initialize Streamlit Cloud cache if running in Streamlit
        self._streamlit_cache = None
        try:
            import streamlit as st
            self._is_streamlit = True
        except ImportError:
            self._is_streamlit = False
        
        self._initialize_db()
    
    def _initialize_db(self):
        """Create database and tables if they don't exist"""
        try:
            if self.use_cloud and self.provider != 'sqlite':
                self._initialize_cloud_db()
            else:
                self._initialize_sqlite_db()
        except Exception as e:
            print(f"Error initializing database: {e}")
            # Fall back to SQLite
            print("Falling back to SQLite...")
            self._initialize_sqlite_db()
    
    def _initialize_sqlite_db(self):
        """Initialize SQLite database"""
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
    
    def _initialize_cloud_db(self):
        """Initialize cloud database (Azure SQL, PostgreSQL, etc.)"""
        try:
            if self.provider == 'azure':
                import pyodbc
                connection_string = self._build_azure_connection_string()
                self.conn = pyodbc.connect(connection_string)
                self.conn.setencoding(encoding='utf-8')
            elif self.provider == 'postgres':
                import psycopg2
                self.conn = psycopg2.connect(
                    host=self.cloud_config['host'],
                    user=self.cloud_config['user'],
                    password=self.cloud_config['password'],
                    database=self.cloud_config['database']
                )
            else:
                raise ValueError(f"Unknown cloud provider: {self.provider}")
            
            # Create tables
            cursor = self.conn.cursor()
            
            # Use provider-specific SQL
            if self.provider == 'azure':
                feedback_sql = '''
                    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='feedback')
                    CREATE TABLE feedback (
                        id INT PRIMARY KEY IDENTITY(1,1),
                        prediction_id INT,
                        prediction_date DATE,
                        predicted_value FLOAT,
                        actual_value FLOAT,
                        feedback_status VARCHAR(50) NOT NULL,
                        user_feedback TEXT,
                        created_at DATETIME DEFAULT GETDATE()
                    )
                '''
                retraining_sql = '''
                    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='retraining_log')
                    CREATE TABLE retraining_log (
                        id INT PRIMARY KEY IDENTITY(1,1),
                        trigger_reason VARCHAR(255) NOT NULL,
                        feedback_count INT,
                        drift_score FLOAT,
                        accuracy_drop FLOAT,
                        model_improvement FLOAT,
                        started_at DATETIME DEFAULT GETDATE(),
                        completed_at DATETIME,
                        status VARCHAR(50) DEFAULT 'pending',
                        metrics_before TEXT,
                        metrics_after TEXT
                    )
                '''
            else:  # PostgreSQL
                feedback_sql = '''
                    CREATE TABLE IF NOT EXISTS feedback (
                        id SERIAL PRIMARY KEY,
                        prediction_id INTEGER,
                        prediction_date DATE,
                        predicted_value FLOAT,
                        actual_value FLOAT,
                        feedback_status VARCHAR(50) NOT NULL,
                        user_feedback TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                '''
                retraining_sql = '''
                    CREATE TABLE IF NOT EXISTS retraining_log (
                        id SERIAL PRIMARY KEY,
                        trigger_reason VARCHAR(255) NOT NULL,
                        feedback_count INTEGER,
                        drift_score FLOAT,
                        accuracy_drop FLOAT,
                        model_improvement FLOAT,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        status VARCHAR(50) DEFAULT 'pending',
                        metrics_before TEXT,
                        metrics_after TEXT
                    )
                '''
            
            cursor.execute(feedback_sql)
            cursor.execute(retraining_sql)
            self.conn.commit()
            cursor.close()
        
        except Exception as e:
            print(f"Error initializing cloud database: {e}")
            raise
    
    def _build_azure_connection_string(self) -> str:
        """Build Azure SQL connection string"""
        return (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={self.cloud_config['host']};"
            f"Database={self.cloud_config['database']};"
            f"UID={self.cloud_config['user']};"
            f"PWD={self.cloud_config['password']};"
            f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
    
    def submit_feedback(
        self,
        prediction_id: Optional[int],
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
            if self.provider == 'sqlite':
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
            else:
                cursor = self.conn.cursor()
                
                if self.provider == 'azure':
                    cursor.execute('''
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
                else:  # PostgreSQL
                    cursor.execute('''
                        INSERT INTO feedback 
                        (prediction_id, prediction_date, predicted_value, actual_value, 
                         feedback_status, user_feedback)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (
                        prediction_id,
                        prediction_date,
                        predicted_value,
                        actual_value,
                        feedback_status,
                        user_feedback
                    ))
                    feedback_id = cursor.fetchone()[0]
                
                self.conn.commit()
                cursor.close()
                return feedback_id if self.provider == 'postgres' else 1
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
        try:
            if self.provider == 'sqlite':
                query = '''
                    SELECT COUNT(*) as count
                    FROM feedback
                    WHERE DATE(created_at) >= DATE('now', '-' || ? || ' days')
                '''
                cursor = self.conn.execute(query, (days,))
                result = cursor.fetchone()
                return result['count'] if result else 0
            else:
                cursor = self.conn.cursor()
                
                if self.provider == 'azure':
                    query = '''
                        SELECT COUNT(*) as count
                        FROM feedback
                        WHERE DATEDIFF(day, created_at, GETDATE()) <= ?
                    '''
                    cursor.execute(query, (days,))
                else:  # PostgreSQL
                    query = '''
                        SELECT COUNT(*) as count
                        FROM feedback
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                    '''
                    cursor.execute(query % days)
                
                result = cursor.fetchone()
                count = result[0] if result else 0
                cursor.close()
                return count
        except Exception as e:
            print(f"Error getting feedback count: {e}")
            return 0
    
    def get_recent_feedback(self, days: int = 30, limit: int = 50) -> pd.DataFrame:
        """
        Get recent feedback submissions
        
        Args:
            days: Number of days to look back
            limit: Maximum number of records to return
        
        Returns:
            DataFrame with feedback records
        """
        try:
            if self.provider == 'sqlite':
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
            else:
                cursor = self.conn.cursor()
                
                if self.provider == 'azure':
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
                        WHERE DATEDIFF(day, created_at, GETDATE()) <= ?
                        ORDER BY created_at DESC
                        OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                    '''
                    cursor.execute(query, (days, limit))
                else:  # PostgreSQL
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
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        ORDER BY created_at DESC
                        LIMIT %s
                    '''
                    cursor.execute(query % (days, limit))
                
                rows = cursor.fetchall()
                cursor.close()
                
                df = pd.DataFrame(rows, columns=[
                    'id', 'prediction_id', 'prediction_date', 'predicted_value',
                    'actual_value', 'feedback_status', 'user_feedback', 'created_at'
                ])
            
            if not df.empty:
                df['prediction_date'] = pd.to_datetime(df['prediction_date'])
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['error'] = abs(df['actual_value'] - df['predicted_value'])
            
            return df
        except Exception as e:
            print(f"Error getting recent feedback: {e}")
            return pd.DataFrame()
    
    def get_feedback_accuracy(self, days: int = 30) -> Dict:
        """
        Calculate accuracy metrics from feedback
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with accuracy metrics
        """
        try:
            if self.provider == 'sqlite':
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
            else:
                cursor = self.conn.cursor()
                
                if self.provider == 'azure':
                    query = '''
                        SELECT 
                            feedback_status,
                            COUNT(*) as count,
                            AVG(ABS(actual_value - predicted_value)) as avg_error
                        FROM feedback
                        WHERE DATEDIFF(day, created_at, GETDATE()) <= ?
                        GROUP BY feedback_status
                    '''
                    cursor.execute(query, (days,))
                else:  # PostgreSQL
                    query = '''
                        SELECT 
                            feedback_status,
                            COUNT(*) as count,
                            AVG(ABS(actual_value - predicted_value)) as avg_error
                        FROM feedback
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY feedback_status
                    '''
                    cursor.execute(query % days)
                
                rows = cursor.fetchall()
                cursor.close()
                
                df = pd.DataFrame(rows, columns=['feedback_status', 'count', 'avg_error'])
            
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
            correct = df[df['feedback_status'] == 'correct']['count'].sum() if not df.empty else 0
            incorrect = df[df['feedback_status'] == 'incorrect']['count'].sum() if not df.empty else 0
            uncertain = df[df['feedback_status'] == 'uncertain']['count'].sum() if not df.empty else 0
            
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
        except Exception as e:
            print(f"Error calculating feedback accuracy: {e}")
            return {
                'total_feedback': 0,
                'correct_feedback': 0,
                'incorrect_feedback': 0,
                'uncertain_feedback': 0,
                'accuracy': 0.0,
                'avg_error': 0.0
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
            if self.provider == 'sqlite':
                cursor = self.conn.execute('''
                    INSERT INTO retraining_log 
                    (trigger_reason, feedback_count, drift_score, accuracy_drop, status)
                    VALUES (?, ?, ?, ?, 'pending')
                ''', (trigger_reason, feedback_count, drift_score, accuracy_drop))
                self.conn.commit()
                return cursor.lastrowid
            else:
                cursor = self.conn.cursor()
                
                if self.provider == 'azure':
                    cursor.execute('''
                        INSERT INTO retraining_log 
                        (trigger_reason, feedback_count, drift_score, accuracy_drop, status)
                        VALUES (?, ?, ?, ?, 'pending')
                    ''', (trigger_reason, feedback_count, drift_score, accuracy_drop))
                else:  # PostgreSQL
                    cursor.execute('''
                        INSERT INTO retraining_log 
                        (trigger_reason, feedback_count, drift_score, accuracy_drop, status)
                        VALUES (%s, %s, %s, %s, 'pending')
                        RETURNING id
                    ''', (trigger_reason, feedback_count, drift_score, accuracy_drop))
                    retraining_id = cursor.fetchone()[0]
                
                self.conn.commit()
                cursor.close()
                return retraining_id if self.provider == 'postgres' else 1
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
            if self.provider == 'sqlite':
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
            else:
                cursor = self.conn.cursor()
                
                if self.provider == 'azure':
                    cursor.execute('''
                        UPDATE retraining_log
                        SET status = 'completed',
                            completed_at = GETDATE(),
                            model_improvement = ?,
                            metrics_before = ?,
                            metrics_after = ?
                        WHERE id = ?
                    ''', (model_improvement, metrics_before, metrics_after, retraining_id))
                else:  # PostgreSQL
                    cursor.execute('''
                        UPDATE retraining_log
                        SET status = 'completed',
                            completed_at = NOW(),
                            model_improvement = %s,
                            metrics_before = %s,
                            metrics_after = %s
                        WHERE id = %s
                    ''', (model_improvement, metrics_before, metrics_after, retraining_id))
                
                self.conn.commit()
                cursor.close()
            
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
        try:
            if self.provider == 'sqlite':
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
            else:
                cursor = self.conn.cursor()
                
                if self.provider == 'azure':
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
                        OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                    '''
                    cursor.execute(query, (limit,))
                else:  # PostgreSQL
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
                        LIMIT %s
                    '''
                    cursor.execute(query % limit)
                
                rows = cursor.fetchall()
                cursor.close()
                
                df = pd.DataFrame(rows, columns=[
                    'id', 'trigger_reason', 'feedback_count', 'drift_score',
                    'accuracy_drop', 'model_improvement', 'status', 'started_at', 'completed_at'
                ])
            
            if not df.empty:
                df['started_at'] = pd.to_datetime(df['started_at'])
                df['completed_at'] = pd.to_datetime(df['completed_at'])
            
            return df
        except Exception as e:
            print(f"Error getting retraining history: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            try:
                self.conn.close()
            except Exception as e:
                print(f"Error closing connection: {e}")

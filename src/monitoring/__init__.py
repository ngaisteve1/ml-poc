"""
Monitoring module for drift detection and prediction tracking

This module provides comprehensive monitoring capabilities:
- predictions_db: SQLite storage for predictions and metrics
- drift_detector: Statistical drift detection (anomalies, distribution, trends)
- alerts: (Planned) Alert management system

Usage:
    from src.monitoring import PredictionsDB, DriftDetector
    
    # Initialize database
    db = PredictionsDB()
    db.save_prediction('2025-01-01', 250.5, 130.2)
    
    # Initialize drift detector
    detector = DriftDetector()
    detector.set_baseline([250, 252, 248, 251, 249, 250, 252, 251, 250, 251])
    
    # Check for drift
    results = detector.check_all_drifts([250, 252, 248, 251, 249])
    print(detector.get_drift_summary(results))
"""

from .predictions_db import PredictionsDB
from .drift_detector import DriftDetector
from .alerts import AlertManager

__all__ = ['PredictionsDB', 'DriftDetector', 'AlertManager']

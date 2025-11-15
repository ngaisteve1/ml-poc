"""
Alert Management Module

Handles creation, persistence, and notification of alerts based on drift detection results.
Provides alert thresholds, severity levels, and notification mechanisms.
"""

import json
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List
from .predictions_db import PredictionsDB


def _convert_to_json_serializable(obj):
    """
    Convert numpy types to native Python types for JSON serialization
    
    Args:
        obj: Object that may contain numpy types
    
    Returns:
        JSON-serializable version of object
    """
    if isinstance(obj, dict):
        return {k: _convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.int_, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    else:
        return obj


class AlertManager:
    """
    Manages alerts based on drift detection results
    
    Responsibilities:
    - Create alerts from drift detection results
    - Determine alert severity and type
    - Persist alerts to database
    - Send notifications (console, email, dashboard)
    - Track alert state and acknowledgment
    
    Alert Severity Levels:
    - 'info': Informational only
    - 'warning': Single drift signal
    - 'critical': Multiple drift signals or severe degradation
    """
    
    # Alert type definitions
    ALERT_TYPES = {
        'anomaly': {
            'name': 'Anomaly Detection',
            'icon': '🔴',
            'default_severity': 'warning'
        },
        'distribution_drift': {
            'name': 'Distribution Drift',
            'icon': '📊',
            'default_severity': 'warning'
        },
        'trend_drift': {
            'name': 'Trend Change',
            'icon': '📈',
            'default_severity': 'warning'
        },
        'multi_signal': {
            'name': 'Multiple Drift Signals',
            'icon': '🚨',
            'default_severity': 'critical'
        }
    }
    
    # Recommendations for each alert type
    RECOMMENDATIONS = {
        'anomaly': 'Check data quality and input features for the anomalous prediction',
        'distribution_drift': 'Consider model retraining with updated data distribution',
        'trend_drift': 'Monitor upcoming predictions closely for further degradation',
        'multi_signal': 'Immediate action required - review model performance and input data'
    }
    
    def __init__(
        self,
        db: PredictionsDB,
        z_score_threshold: float = 2.0,
        ks_p_value_threshold: float = 0.05,
        trend_change_threshold: float = 10.0,
        anomaly_alert_threshold: int = 2
    ):
        """
        Initialize alert manager with drift detection thresholds
        
        Args:
            db: PredictionsDB instance for persistence
            z_score_threshold: Z-score threshold for anomaly (default: 2.0)
            ks_p_value_threshold: KS test p-value threshold (default: 0.05)
            trend_change_threshold: Trend change % threshold (default: 10.0)
            anomaly_alert_threshold: Anomaly count threshold for alert (default: 2)
        """
        self.db = db
        self.z_score_threshold = z_score_threshold
        self.ks_p_value_threshold = ks_p_value_threshold
        self.trend_change_threshold = trend_change_threshold
        self.anomaly_alert_threshold = anomaly_alert_threshold
    
    def create_alert_from_drift(
        self,
        drift_results: Dict,
        prediction_date: str
    ) -> Optional[Dict]:
        """
        Create alert from drift detection results
        
        Analyzes drift detection results and creates an alert if drift is detected.
        Determines alert type, severity, and appropriate message.
        
        Args:
            drift_results: Dictionary from DriftDetector.check_all_drifts()
            prediction_date: Date of the prediction (YYYY-MM-DD)
        
        Returns:
            Alert dictionary or None if no drift:
            {
                'alert_type': str ('anomaly', 'distribution_drift', 'trend_drift', 'multi_signal'),
                'severity': str ('info', 'warning', 'critical'),
                'message': str (user-friendly message),
                'details': Dict (drift detection results),
                'recommendation': str (action to take),
                'prediction_date': str (YYYY-MM-DD),
                'created_at': str (ISO timestamp),
                'status': 'active'
            }
        """
        if not drift_results.get('overall_drift_detected', False):
            return None
        
        # Determine alert type
        alert_type = self._determine_alert_type(drift_results)
        
        # Calculate severity
        severity = self._calculate_severity(drift_results, alert_type)
        
        # Generate message
        message = self._generate_message(alert_type, drift_results)
        
        # Get recommendation
        recommendation = self._get_recommendation(alert_type)
        
        return {
            'alert_type': alert_type,
            'severity': severity,
            'message': message,
            'details': drift_results,
            'recommendation': recommendation,
            'prediction_date': prediction_date,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
    
    def _determine_alert_type(self, drift_results: Dict) -> str:
        """
        Determine alert type based on drift detection signals
        
        Args:
            drift_results: Dictionary from DriftDetector.check_all_drifts()
        
        Returns:
            Alert type string ('anomaly', 'distribution_drift', 'trend_drift', 'multi_signal')
        """
        anomalies = drift_results.get('anomalies', {})
        distribution = drift_results.get('distribution_drift', {})
        trend = drift_results.get('trend_drift', {})
        
        # Count drift signals
        signals = 0
        primary_type = None
        
        # Check for anomalies
        if anomalies.get('has_anomalies', False) and anomalies.get('anomaly_count', 0) >= self.anomaly_alert_threshold:
            signals += 1
            primary_type = 'anomaly'
        
        # Check for distribution drift
        if distribution.get('has_drift', False):
            signals += 1
            if primary_type is None:
                primary_type = 'distribution_drift'
        
        # Check for trend drift
        if trend.get('has_trend_drift', False):
            signals += 1
            if primary_type is None:
                primary_type = 'trend_drift'
        
        # Determine final type
        if signals >= 2:
            return 'multi_signal'
        elif primary_type:
            return primary_type
        else:
            # Default if no clear signal (shouldn't happen)
            return 'anomaly'
    
    def _calculate_severity(self, drift_results: Dict, alert_type: str) -> str:
        """
        Calculate alert severity level
        
        Args:
            drift_results: Drift detection results
            alert_type: Type of alert
        
        Returns:
            Severity level ('info', 'warning', 'critical')
        """
        # Multi-signal always critical
        if alert_type == 'multi_signal':
            return 'critical'
        
        # Check severity indicators
        anomalies = drift_results.get('anomalies', {})
        distribution = drift_results.get('distribution_drift', {})
        trend = drift_results.get('trend_drift', {})
        
        # High z-score = warning
        if anomalies.get('max_z_score', 0) > 3.0:
            return 'critical'
        
        # Very low p-value = critical
        if distribution.get('p_value', 1.0) < 0.01:
            return 'critical'
        
        # Large mean shift = warning
        if abs(distribution.get('mean_change_pct', 0)) > 15:
            return 'warning'
        
        # Large trend change = warning
        if abs(trend.get('trend_change_pct', 0)) > 15:
            return 'warning'
        
        # Default to warning for detected drift
        return 'warning'
    
    def _generate_message(self, alert_type: str, drift_results: Dict) -> str:
        """
        Generate human-readable alert message
        
        Args:
            alert_type: Type of alert
            drift_results: Drift detection results
        
        Returns:
            Formatted message string
        """
        if alert_type == 'anomaly':
            anomalies = drift_results.get('anomalies', {})
            count = anomalies.get('anomaly_count', 0)
            z_score = anomalies.get('max_z_score', 0)
            return f"Anomaly detected: {count} outlier(s) found (max z-score: {z_score:.2f})"
        
        elif alert_type == 'distribution_drift':
            distribution = drift_results.get('distribution_drift', {})
            p_value = distribution.get('p_value', 0)
            change = distribution.get('mean_change_pct', 0)
            return f"Distribution shift detected (p={p_value:.4f}, mean change: {change:+.1f}%)"
        
        elif alert_type == 'trend_drift':
            trend = drift_results.get('trend_drift', {})
            direction = trend.get('trend_direction', 'unknown')
            change = trend.get('trend_change_pct', 0)
            return f"Trend change detected: {direction.upper()} ({change:+.1f}%)"
        
        elif alert_type == 'multi_signal':
            anomalies = drift_results.get('anomalies', {})
            distribution = drift_results.get('distribution_drift', {})
            trend = drift_results.get('trend_drift', {})
            
            signals = []
            if anomalies.get('has_anomalies', False):
                signals.append(f"{anomalies.get('anomaly_count', 0)} anomalies")
            if distribution.get('has_drift', False):
                signals.append("distribution shift")
            if trend.get('has_trend_drift', False):
                signals.append("trend change")
            
            return f"Multiple drift signals: {', '.join(signals)}"
        
        return "Drift detected"
    
    def _get_recommendation(self, alert_type: str) -> str:
        """Get recommendation for alert type"""
        return self.RECOMMENDATIONS.get(alert_type, "Review model performance")
    
    def save_alert(self, alert: Dict) -> int:
        """
        Save alert to database as monitoring event
        
        Args:
            alert: Alert dictionary
        
        Returns:
            Event ID if successful, -1 if error
        """
        try:
            # Convert drift details to JSON-serializable format
            drift_details = {
                'anomalies': alert.get('details', {}).get('anomalies', {}),
                'distribution_drift': alert.get('details', {}).get('distribution_drift', {}),
                'trend_drift': alert.get('details', {}).get('trend_drift', {})
            }
            drift_details = _convert_to_json_serializable(drift_details)
            
            event_id = self.db.save_monitoring_event(
                event_type='alert',
                event_severity=alert.get('severity', 'warning'),
                message=alert.get('message', 'Alert created'),
                metadata=json.dumps({
                    'alert_type': alert.get('alert_type'),
                    'recommendation': alert.get('recommendation'),
                    'prediction_date': alert.get('prediction_date'),
                    'drift_details': drift_details
                })
            )
            return event_id
        except Exception as e:
            print(f"Error saving alert: {e}")
            return -1
    
    def get_active_alerts(self, days: int = 7) -> list:
        """
        Get active/unacknowledged alerts from recent days
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of alert dictionaries
        """
        try:
            events = self.db.get_monitoring_events(days=days, event_type='alert')
            
            alerts = []
            for _, event in events.iterrows():
                try:
                    metadata = json.loads(event['metadata']) if event['metadata'] else {}
                    alerts.append({
                        'id': event['id'],
                        'severity': event['event_severity'],
                        'message': event['message'],
                        'alert_type': metadata.get('alert_type'),
                        'recommendation': metadata.get('recommendation'),
                        'created_at': event['created_at'],
                        'prediction_date': metadata.get('prediction_date')
                    })
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return alerts
        except Exception as e:
            print(f"Error retrieving alerts: {e}")
            return []
    
    def get_alert_summary(self, days: int = 7) -> Dict:
        """
        Get summary statistics of recent alerts
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with alert counts by severity and type
        """
        alerts = self.get_active_alerts(days=days)
        
        summary = {
            'total_alerts': len(alerts),
            'critical_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'by_type': {}
        }
        
        for alert in alerts:
            severity = alert.get('severity', 'info')
            alert_type = alert.get('alert_type', 'unknown')
            
            if severity == 'critical':
                summary['critical_count'] += 1
            elif severity == 'warning':
                summary['warning_count'] += 1
            else:
                summary['info_count'] += 1
            
            if alert_type not in summary['by_type']:
                summary['by_type'][alert_type] = 0
            summary['by_type'][alert_type] += 1
        
        return summary
    
    def send_notification(self, alert: Dict) -> bool:
        """
        Send alert notification (console and/or email)
        
        Args:
            alert: Alert dictionary
        
        Returns:
            True if notification sent successfully
        """
        try:
            severity = alert.get('severity', 'warning')
            message = alert.get('message', '')
            recommendation = alert.get('recommendation', '')
            
            # Console notification
            self._send_console_notification(alert)
            
            # Future: Email notification
            # self._send_email_notification(alert)
            
            return True
        except Exception as e:
            print(f"Error sending notification: {e}")
            return False
    
    def _send_console_notification(self, alert: Dict):
        """Send alert to console with formatting"""
        severity = alert.get('severity', 'warning')
        message = alert.get('message', '')
        recommendation = alert.get('recommendation', '')
        alert_type = alert.get('alert_type', '')
        
        # Severity icons
        severity_icons = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        icon = severity_icons.get(severity, '•')
        
        print(f"\n{icon} ALERT [{severity.upper()}]")
        print(f"   Type: {alert_type}")
        print(f"   Message: {message}")
        print(f"   Action: {recommendation}")
        print(f"   Time: {alert.get('created_at', 'N/A')}\n")
    
    def _send_email_notification(self, alert: Dict) -> bool:
        """
        Send email notification (stub for future implementation)
        
        Would require:
        - SMTP configuration
        - Email templates
        - Recipient configuration
        
        Args:
            alert: Alert dictionary
        
        Returns:
            True if email sent
        """
        # TODO: Implement email notification
        # This would be added in a future phase
        return False
    
    def acknowledge_alert(self, event_id: int) -> bool:
        """
        Mark alert as acknowledged (stub for future implementation)
        
        Args:
            event_id: ID of the event/alert
        
        Returns:
            True if acknowledgment saved
        """
        # TODO: Add acknowledgment support to database
        # Would require adding 'acknowledged' column to monitoring_events
        return False
    
    def get_alert_history(self, days: int = 30, severity: Optional[str] = None) -> List[Dict]:
        """
        Get historical alerts with optional severity filter
        
        Args:
            days: Number of days to retrieve
            severity: Optional filter ('critical', 'warning', 'info')
        
        Returns:
            List of alert dictionaries
        """
        try:
            events = self.db.get_monitoring_events(days=days, event_type='alert', severity=severity)
            
            alerts = []
            for _, event in events.iterrows():
                try:
                    metadata = json.loads(event['metadata']) if event['metadata'] else {}
                    alerts.append({
                        'id': event['id'],
                        'severity': event['event_severity'],
                        'message': event['message'],
                        'alert_type': metadata.get('alert_type'),
                        'recommendation': metadata.get('recommendation'),
                        'created_at': event['created_at'],
                        'prediction_date': metadata.get('prediction_date')
                    })
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return alerts
        except Exception as e:
            print(f"Error retrieving alert history: {e}")
            return []


if __name__ == "__main__":
    """Test alert manager functionality"""
    from .drift_detector import DriftDetector
    import numpy as np
    
    print("Testing AlertManager...")
    print("=" * 60)
    
    # Initialize components
    db = PredictionsDB('test_alerts_db.db')
    manager = AlertManager(db)
    
    # Test 1: Create alert from drift results
    print("\n✓ Test 1: Alert creation from drift results")
    drift_results = {
        'overall_drift_detected': True,
        'anomalies': {
            'has_anomalies': True,
            'anomaly_count': 3,
            'max_z_score': 2.5
        },
        'distribution_drift': {
            'has_drift': False,
            'p_value': 0.87
        },
        'trend_drift': {
            'has_trend_drift': False
        }
    }
    
    alert = manager.create_alert_from_drift(drift_results, '2025-11-14')
    print(f"  Alert type: {alert['alert_type']}")
    print(f"  Severity: {alert['severity']}")
    print(f"  Message: {alert['message']}")
    print(f"  Recommendation: {alert['recommendation']}")
    
    # Test 2: Save alert
    print("\n✓ Test 2: Saving alert to database")
    alert_id = manager.save_alert(alert)
    print(f"  Alert saved with ID: {alert_id}")
    assert alert_id > 0, "Alert should be saved successfully"
    
    # Test 3: Multi-signal alert
    print("\n✓ Test 3: Multi-signal alert creation")
    multi_drift = {
        'overall_drift_detected': True,
        'anomalies': {
            'has_anomalies': True,
            'anomaly_count': 4,
            'max_z_score': 3.1
        },
        'distribution_drift': {
            'has_drift': True,
            'p_value': 0.01,
            'mean_change_pct': 20.5
        },
        'trend_drift': {
            'has_trend_drift': True,
            'trend_direction': 'up',
            'trend_change_pct': 15.2
        }
    }
    
    multi_alert = manager.create_alert_from_drift(multi_drift, '2025-11-14')
    print(f"  Alert type: {multi_alert['alert_type']}")
    print(f"  Severity: {multi_alert['severity']}")
    print(f"  Message: {multi_alert['message']}")
    assert multi_alert['alert_type'] == 'multi_signal', "Should detect multi-signal"
    assert multi_alert['severity'] == 'critical', "Should be critical severity"
    
    manager.save_alert(multi_alert)
    
    # Test 4: Get active alerts
    print("\n✓ Test 4: Retrieving active alerts")
    active = manager.get_active_alerts(days=1)
    print(f"  Active alerts: {len(active)}")
    for a in active:
        print(f"    - [{a['severity'].upper()}] {a['message']}")
    
    # Test 5: Get alert summary
    print("\n✓ Test 5: Alert summary statistics")
    summary = manager.get_alert_summary(days=1)
    print(f"  Total alerts: {summary['total_alerts']}")
    print(f"  Critical: {summary['critical_count']}")
    print(f"  Warning: {summary['warning_count']}")
    print(f"  By type: {summary['by_type']}")
    
    # Test 6: Send notifications
    print("\n✓ Test 6: Sending notifications")
    manager.send_notification(alert)
    manager.send_notification(multi_alert)
    
    # Test 7: No drift = no alert
    print("\n✓ Test 7: No alert when no drift")
    no_drift = {
        'overall_drift_detected': False,
        'anomalies': {'has_anomalies': False},
        'distribution_drift': {'has_drift': False},
        'trend_drift': {'has_trend_drift': False}
    }
    
    no_alert = manager.create_alert_from_drift(no_drift, '2025-11-14')
    print(f"  Alert created: {no_alert is not None}")
    assert no_alert is None, "Should not create alert when no drift"
    
    # Cleanup
    db.close()
    import os
    if os.path.exists('test_alerts_db.db'):
        os.remove('test_alerts_db.db')
    
    print("\n" + "=" * 60)
    print("✅ All alert manager tests passed!")

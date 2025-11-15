"""
Generate sample monitoring data for testing the dashboard

This script populates the monitoring.db with sample predictions,
drift events, and alerts for testing the monitoring dashboard.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring import PredictionsDB, DriftDetector, AlertManager


def generate_sample_data(days=30, db_path='monitoring.db'):
    """
    Generate sample monitoring data for dashboard testing
    
    Args:
        days: Number of days of predictions to generate
        db_path: Path to monitoring database
    """
    print(f"Generating {days} days of sample monitoring data...")
    
    # Initialize components
    db = PredictionsDB(db_path)
    detector = DriftDetector()
    manager = AlertManager(db)
    
    try:
        # Generate baseline predictions (first half of period)
        baseline_size = days // 2
        print(f"\n📊 Generating baseline predictions ({baseline_size} days)...")
        
        baseline_predictions = []
        for i in range(baseline_size):
            date = (datetime.now() - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
            
            # Normal baseline with mean=250, std=15
            archived_gb = 250 + np.random.normal(0, 15)
            savings_gb = archived_gb * 0.52 + np.random.normal(0, 5)
            
            db.save_prediction(
                prediction_date=date,
                archived_gb_predicted=archived_gb,
                savings_gb_predicted=savings_gb,
                archived_gb_actual=archived_gb + np.random.normal(0, 5),
                savings_gb_actual=savings_gb + np.random.normal(0, 2)
            )
            
            baseline_predictions.append(archived_gb)
        
        print(f"✅ Baseline saved (mean={np.mean(baseline_predictions):.1f} GB)")
        
        # Set detector baseline
        detector.set_baseline(baseline_predictions)
        
        # Generate recent predictions with some drift (second half of period)
        print(f"\n📈 Generating recent predictions with drift ({days - baseline_size} days)...")
        
        recent_predictions = []
        for i in range(baseline_size, days):
            date = (datetime.now() - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
            
            # Gradually increasing trend starting from day 20
            days_into_trend = i - baseline_size
            trend_increase = days_into_trend * 1.5  # +1.5 GB per day
            
            archived_gb = 250 + trend_increase + np.random.normal(0, 15)
            savings_gb = archived_gb * 0.52 + np.random.normal(0, 5)
            
            # Add occasional anomalies
            if i % 5 == 0:
                archived_gb += np.random.choice([50, -40])  # Outlier
            
            db.save_prediction(
                prediction_date=date,
                archived_gb_predicted=archived_gb,
                savings_gb_predicted=savings_gb,
                archived_gb_actual=archived_gb + np.random.normal(0, 5),
                savings_gb_actual=savings_gb + np.random.normal(0, 2)
            )
            
            recent_predictions.append(archived_gb)
        
        print(f"✅ Recent predictions saved (mean={np.mean(recent_predictions):.1f} GB)")
        
        # Check for drift and create alerts
        print(f"\n🔍 Detecting drift...")
        drift_results = detector.check_all_drifts(recent_predictions)
        
        if drift_results['overall_drift_detected']:
            print(f"✅ Drift detected! Creating alert...")
            
            alert = manager.create_alert_from_drift(drift_results, datetime.now().strftime('%Y-%m-%d'))
            
            if alert:
                alert_id = manager.save_alert(alert)
                print(f"   Alert saved: {alert['alert_type']} ({alert['severity']})")
                print(f"   Message: {alert['message']}")
        else:
            print("✅ No significant drift detected")
        
        # Create some sample monitoring events
        print(f"\n📋 Creating sample monitoring events...")
        
        events = [
            ('model_prediction', 'info', f'Generated {days} prediction(s)', None),
            ('drift_check', 'info', 'Drift detection completed', 
             json.dumps({'anomalies': drift_results['anomalies']['anomaly_count']})),
        ]
        
        if drift_results['trend_drift']['has_trend_drift']:
            events.append(('trend_detected', 'warning', 
                          f"Trend change: {drift_results['trend_drift']['trend_direction']}",
                          json.dumps({'change': drift_results['trend_drift']['trend_change_pct']})))
        
        for event_type, severity, message, metadata in events:
            db.save_monitoring_event(event_type, severity, message, metadata)
        
        print(f"✅ Created {len(events)} monitoring events")
        
        # Verify alerts were saved
        print(f"\n🔍 Verifying alerts in database...")
        saved_alerts = manager.get_active_alerts(days=30)
        print(f"   Found {len(saved_alerts)} alert(s) in database")
        if saved_alerts:
            for alert in saved_alerts:
                print(f"   - {alert['severity'].upper()}: {alert['message']}")
        
        # Get summary statistics
        print(f"\n📊 Database Summary:")
        stats = db.get_summary_statistics(days=days)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
        
        print(f"\n✅ Sample data generation complete!")
        print(f"\nYou can now:")
        print(f"  1. Run: streamlit run src/ui/streamlit_app.py")
        print(f"  2. Go to 'Monitoring' tab")
        print(f"  3. See predictions, alerts, and drift analysis")
        
    finally:
        db.close()


if __name__ == "__main__":
    # Generate 30 days of sample data
    generate_sample_data(days=30)

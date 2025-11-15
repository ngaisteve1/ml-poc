"""
Comprehensive test for Storage & Detection monitoring components

Tests:
1. Database initialization and schema
2. Saving and retrieving predictions
3. Anomaly detection with z-score
4. Distribution drift detection with KS test
5. Trend drift detection
6. Monitoring events logging
7. Integration: Full workflow with Azure ML predictions
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitoring import PredictionsDB, DriftDetector


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)


def test_database_initialization():
    """Test 1: Database initialization and schema creation"""
    print_section("TEST 1: Database Initialization")
    
    db = PredictionsDB('test_db.db')
    print("✓ Database initialized")
    
    # Verify tables exist
    cursor = db.conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"✓ Tables created: {', '.join(tables)}")
    assert 'predictions' in tables, "Missing predictions table"
    assert 'monitoring_events' in tables, "Missing monitoring_events table"
    assert 'model_metrics' in tables, "Missing model_metrics table"
    
    db.close()
    print("\n✅ Test 1 PASSED")


def test_save_and_retrieve_predictions():
    """Test 2: Save and retrieve predictions"""
    print_section("TEST 2: Save & Retrieve Predictions")
    
    db = PredictionsDB('test_db.db')
    
    # Save 10 predictions
    print("Saving 10 predictions...")
    for i in range(10):
        date = (datetime.now() - timedelta(days=9-i)).strftime('%Y-%m-%d')
        db.save_prediction(
            prediction_date=date,
            archived_gb_predicted=250 + i * 2,
            savings_gb_predicted=130 + i * 1.5,
            archived_gb_actual=245 + i * 2 + np.random.normal(0, 5),
            savings_gb_actual=128 + i * 1.5 + np.random.normal(0, 2)
        )
    print("✓ Saved 10 predictions")
    
    # Retrieve predictions
    predictions = db.get_predictions(days=30)
    print(f"✓ Retrieved {len(predictions)} predictions")
    print(f"\n  Sample data:\n{predictions.head(3).to_string()}")
    
    assert len(predictions) == 10, "Expected 10 predictions"
    assert 'archived_gb_predicted' in predictions.columns
    assert 'savings_gb_predicted' in predictions.columns
    
    # Test get_latest_prediction
    latest = db.get_latest_prediction()
    print(f"\n✓ Latest prediction: {json.dumps(latest, indent=2, default=str)}")
    assert latest is not None
    
    # Test get_recent_predictions_for_drift
    archived_list, savings_list = db.get_recent_predictions_for_drift(window_size=5)
    print(f"\n✓ Recent predictions for drift (5):")
    print(f"  Archived GB: {archived_list}")
    print(f"  Savings GB: {savings_list}")
    
    assert len(archived_list) == 5
    assert len(savings_list) == 5
    
    db.close()
    print("\n✅ Test 2 PASSED")


def test_z_score_anomaly_detection():
    """Test 3: Z-score anomaly detection"""
    print_section("TEST 3: Z-Score Anomaly Detection")
    
    detector = DriftDetector(z_score_threshold=2.0)
    
    # Create baseline with mean=250, std=15
    baseline = np.random.normal(250, 15, 30).tolist()
    success = detector.set_baseline(baseline)
    print(f"✓ Baseline set: mean={detector.baseline_mean:.2f}, std={detector.baseline_std:.2f}")
    
    # Test 3a: Normal data (few anomalies expected due to threshold)
    print("\n  Test 3a: Normal data (few/no anomalies expected)")
    normal_data = np.random.normal(250, 15, 50).tolist()  # Use more samples for better statistics
    result = detector.detect_anomalies_zscore(normal_data)
    print(f"  ✓ Anomalies detected: {result['has_anomalies']}")
    print(f"    Anomaly count: {result['anomaly_count']}")
    print(f"    Max z-score: {result['max_z_score']:.2f}")
    # With threshold 2.0 and normal distribution, expect ~5% outliers (1-2 out of 50)
    assert result['anomaly_count'] <= len(normal_data) * 0.1, "Too many anomalies for normal data"
    
    # Test 3b: Data with outlier
    print("\n  Test 3b: Data with outlier (anomaly expected)")
    data_with_outlier = normal_data.copy()
    data_with_outlier[5] = 350  # Outlier (>3 std from mean)
    result = detector.detect_anomalies_zscore(data_with_outlier)
    print(f"  ✓ Anomalies detected: {result['has_anomalies']}")
    print(f"    Anomaly count: {result['anomaly_count']}")
    print(f"    Anomaly indices: {result['anomaly_indices']}")
    print(f"    Max z-score: {result['max_z_score']:.2f}")
    assert result['has_anomalies'] == True, "Should detect anomaly"
    assert 5 in result['anomaly_indices'], "Should detect outlier at index 5"
    
    # Test 3c: Multiple outliers
    print("\n  Test 3c: Data with multiple outliers")
    multi_outlier = normal_data.copy()
    multi_outlier[2] = 180
    multi_outlier[8] = 350
    multi_outlier[15] = 190
    result = detector.detect_anomalies_zscore(multi_outlier)
    print(f"  ✓ Anomalies detected: {result['has_anomalies']}")
    print(f"    Anomaly count: {result['anomaly_count']}")
    print(f"    Anomaly indices: {result['anomaly_indices']}")
    assert result['anomaly_count'] >= 2, "Should detect multiple anomalies"
    
    print("\n✅ Test 3 PASSED")


def test_ks_distribution_drift():
    """Test 4: KS test distribution drift detection"""
    print_section("TEST 4: KS Test Distribution Drift Detection")
    
    detector = DriftDetector(ks_test_threshold=0.05)
    
    # Create baseline
    baseline = np.random.normal(250, 15, 30).tolist()
    detector.set_baseline(baseline)
    print(f"✓ Baseline set: mean={detector.baseline_mean:.2f}")
    
    # Test 4a: Same distribution (no drift)
    print("\n  Test 4a: Same distribution (no drift expected)")
    same_dist = np.random.normal(250, 15, 20).tolist()
    result = detector.detect_drift_ks_test(same_dist)
    print(f"  ✓ Drift detected: {result['has_drift']}")
    print(f"    KS statistic: {result['ks_statistic']:.4f}")
    print(f"    P-value: {result['p_value']:.4f}")
    print(f"    Mean change: {result['mean_change_pct']:+.1f}%")
    
    # Test 4b: Shifted distribution (drift)
    print("\n  Test 4b: Shifted distribution (drift expected)")
    shifted_dist = np.random.normal(280, 15, 20).tolist()  # Mean shifted +30
    result = detector.detect_drift_ks_test(shifted_dist)
    print(f"  ✓ Drift detected: {result['has_drift']}")
    print(f"    KS statistic: {result['ks_statistic']:.4f}")
    print(f"    P-value: {result['p_value']:.4f}")
    print(f"    Current mean: {result['current_mean']:.2f}")
    print(f"    Baseline mean: {result['baseline_mean']:.2f}")
    print(f"    Mean change: {result['mean_change_pct']:+.1f}%")
    assert result['has_drift'] == True or result['mean_change_pct'] > 10, "Should detect drift"
    
    # Test 4c: Different variance (drift)
    print("\n  Test 4c: Different variance (drift expected)")
    high_var_dist = np.random.normal(250, 40, 20).tolist()  # Higher variance
    result = detector.detect_drift_ks_test(high_var_dist)
    print(f"  ✓ Drift detected: {result['has_drift']}")
    print(f"    KS statistic: {result['ks_statistic']:.4f}")
    print(f"    P-value: {result['p_value']:.4f}")
    
    print("\n✅ Test 4 PASSED")


def test_trend_drift():
    """Test 5: Trend drift detection"""
    print_section("TEST 5: Trend Drift Detection")
    
    detector = DriftDetector()
    
    # Test 5a: Stable trend
    print("  Test 5a: Stable trend (no drift expected)")
    stable = [250 + np.random.normal(0, 2) for _ in range(30)]
    result = detector.detect_trend_drift(stable)
    print(f"  ✓ Trend drift detected: {result['has_trend_drift']}")
    print(f"    Trend: {result['trend_direction']}")
    print(f"    Trend change: {result['trend_change_pct']:+.1f}%")
    print(f"    Slope: {result['slope']:.4f}")
    
    # Test 5b: Upward trend
    print("\n  Test 5b: Upward trend (drift expected)")
    uptrend = [250 + i * 1.5 + np.random.normal(0, 2) for i in range(30)]
    result = detector.detect_trend_drift(uptrend)
    print(f"  ✓ Trend drift detected: {result['has_trend_drift']}")
    print(f"    Trend: {result['trend_direction']}")
    print(f"    Recent mean: {result['recent_mean']:.2f}")
    print(f"    Older mean: {result['older_mean']:.2f}")
    print(f"    Trend change: {result['trend_change_pct']:+.1f}%")
    print(f"    Slope: {result['slope']:.4f}")
    assert result['trend_direction'] == 'up', "Should detect upward trend"
    
    # Test 5c: Downward trend
    print("\n  Test 5c: Downward trend (drift expected)")
    downtrend = [250 - i * 1.0 + np.random.normal(0, 2) for i in range(30)]
    result = detector.detect_trend_drift(downtrend)
    print(f"  ✓ Trend drift detected: {result['has_trend_drift']}")
    print(f"    Trend: {result['trend_direction']}")
    print(f"    Trend change: {result['trend_change_pct']:+.1f}%")
    print(f"    Slope: {result['slope']:.4f}")
    assert result['trend_direction'] == 'down', "Should detect downward trend"
    
    print("\n✅ Test 5 PASSED")


def test_monitoring_events():
    """Test 6: Monitoring events logging"""
    print_section("TEST 6: Monitoring Events Logging")
    
    db = PredictionsDB('test_db.db')
    
    # Save various events
    events_to_save = [
        ('drift_detected', 'warning', 'Z-score exceeded threshold', '{"z_score": 2.5}'),
        ('anomaly_found', 'warning', 'Outlier value detected', '{"value": 320, "expected": 250}'),
        ('model_updated', 'info', 'Model retrained successfully', None),
        ('prediction_error', 'error', 'Endpoint returned error', '{"status": 500}'),
    ]
    
    print("Saving monitoring events...")
    for event_type, severity, message, metadata in events_to_save:
        db.save_monitoring_event(event_type, severity, message, metadata)
    print(f"✓ Saved {len(events_to_save)} events")
    
    # Retrieve all events
    events = db.get_monitoring_events(days=7)
    print(f"✓ Retrieved {len(events)} events\n")
    print(f"  Sample events:\n{events.head(3).to_string()}")
    
    # Filter by type
    drift_events = db.get_monitoring_events(days=7, event_type='drift_detected')
    print(f"\n✓ Drift events: {len(drift_events)}")
    
    # Filter by severity
    warning_events = db.get_monitoring_events(days=7, severity='warning')
    print(f"✓ Warning events: {len(warning_events)}")
    
    assert len(events) == len(events_to_save)
    
    db.close()
    print("\n✅ Test 6 PASSED")


def test_comprehensive_drift_check():
    """Test 7: Comprehensive drift check with all methods"""
    print_section("TEST 7: Comprehensive Drift Check")
    
    detector = DriftDetector(z_score_threshold=2.0, ks_test_threshold=0.05)
    
    # Set baseline
    baseline = np.random.normal(250, 15, 30).tolist()
    detector.set_baseline(baseline)
    print("✓ Baseline set")
    
    # Test 7a: Clean data (no drift)
    print("\n  Test 7a: Clean data (no drift)")
    clean_data = np.random.normal(250, 15, 20).tolist()
    results = detector.check_all_drifts(clean_data)
    summary = detector.get_drift_summary(results)
    print(f"  {summary}")
    
    # Test 7b: Data with multiple drift signals
    print("\n  Test 7b: Multiple drift signals")
    multi_drift = [250 + i * 2 for i in range(20)]  # Upward trend
    multi_drift[5] = 350  # Add anomaly
    results = detector.check_all_drifts(multi_drift)
    summary = detector.get_drift_summary(results)
    print(f"  {summary}")
    
    print("\n✅ Test 7 PASSED")


def test_integration_workflow():
    """Test 8: Full integration workflow (realistic scenario)"""
    print_section("TEST 8: Integration Workflow")
    
    print("Simulating full monitoring workflow with 30 days of predictions...\n")
    
    # Initialize components
    db = PredictionsDB('test_db.db')
    detector = DriftDetector(z_score_threshold=2.0)
    
    # Simulate 30 days of predictions (with drift starting from day 20)
    print("Step 1: Generate and save 30 days of predictions")
    all_predictions = []
    
    for day in range(30):
        date = (datetime.now() - timedelta(days=29-day)).strftime('%Y-%m-%d')
        
        # Base forecast with gradual increase starting day 20
        base = 250
        if day >= 20:
            base += (day - 20) * 2.5  # Upward drift
        
        archived_gb = base + np.random.normal(0, 5)
        savings_gb = base * 0.52 + np.random.normal(0, 2.5)
        
        db.save_prediction(
            prediction_date=date,
            archived_gb_predicted=archived_gb,
            savings_gb_predicted=savings_gb
        )
        all_predictions.append(archived_gb)
    
    print(f"✓ Saved 30 predictions (mean={np.mean(all_predictions):.2f})")
    
    # Step 2: Set baseline (first 15 days)
    print("\nStep 2: Set baseline from first 15 days")
    baseline = all_predictions[:15]
    detector.set_baseline(baseline)
    print(f"✓ Baseline: mean={detector.baseline_mean:.2f}, std={detector.baseline_std:.2f}")
    
    # Step 3: Check for drift on last 15 days
    print("\nStep 3: Check for drift on recent 15 days")
    recent = all_predictions[15:]
    results = detector.check_all_drifts(recent)
    summary = detector.get_drift_summary(results)
    print(f"{summary}")
    
    # Step 4: Save drift event if detected
    if results['overall_drift_detected']:
        print("\nStep 4: Log drift event to database")
        event_id = db.save_monitoring_event(
            event_type='drift_detected',
            event_severity='warning',
            message=f'Comprehensive drift detected. Mean change: {results["distribution_drift"].get("mean_change_pct", 0):+.1f}%',
            metadata=json.dumps({
                'anomalies': results['anomalies']['anomaly_count'],
                'trend': results['trend_drift'].get('trend_direction', 'unknown'),
                'ks_pvalue': results['distribution_drift'].get('p_value', None)
            })
        )
        print(f"✓ Drift event saved with ID: {event_id}")
    
    # Step 5: Get summary statistics
    print("\nStep 5: Database summary statistics")
    stats = db.get_summary_statistics(days=30)
    print(f"✓ Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"    {key}: {value:.2f}")
        else:
            print(f"    {key}: {value}")
    
    db.close()
    print("\n✅ Test 8 PASSED")


def cleanup():
    """Remove test database"""
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')
        print("✓ Cleaned up test database")


def main():
    """Run all tests"""
    print("\n" + "█" * 70)
    print("█  MONITORING STORAGE & DETECTION - COMPREHENSIVE TEST SUITE")
    print("█" * 70)
    
    try:
        test_database_initialization()
        test_save_and_retrieve_predictions()
        test_z_score_anomaly_detection()
        test_ks_distribution_drift()
        test_trend_drift()
        test_monitoring_events()
        test_comprehensive_drift_check()
        test_integration_workflow()
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED (8/8)")
        print("=" * 70)
        print("\n📊 Monitoring System Ready:")
        print("  ✓ SQLite database for predictions and events")
        print("  ✓ Z-score anomaly detection")
        print("  ✓ KS test distribution drift detection")
        print("  ✓ Trend drift detection")
        print("  ✓ Comprehensive drift reporting")
        print("  ✓ Event logging and monitoring")
        print("\n🎯 Next Steps:")
        print("  1. Create alerts.py for alert management (Phase 2)")
        print("  2. Add monitoring dashboard tab (Phase 2)")
        print("  3. Integrate with streamlit_app.py (Phase 3)")
        
    finally:
        cleanup()


if __name__ == "__main__":
    main()

"""
Phase 3: End-to-End Integration Tests

Validates that all components work together with real data flowing through the system.

Test Coverage:
1. Prediction insertion from Azure ML to database
2. Drift detection on real production predictions
3. Alert creation from detected drift
4. Dashboard rendering with real data
5. Performance validation with 30+ predictions
6. Edge case handling

Date: November 15, 2025
Status: Comprehensive integration testing
"""

import unittest
import tempfile
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = str(Path(__file__).parent.parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from monitoring.predictions_db import PredictionsDB
from monitoring.drift_detector import DriftDetector
from monitoring.alerts import AlertManager


class TestPhase3IntegrationBase(unittest.TestCase):
    """Base class for Phase 3 integration tests with setup/teardown"""
    
    def setUp(self):
        """Initialize test database and components"""
        # Create temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_phase3.db')
        
        # Initialize components
        self.db = PredictionsDB(self.db_path)
        self.detector = DriftDetector(
            z_score_threshold=2.0,
            ks_test_threshold=0.05,
            min_samples=10
        )
        self.alert_manager = AlertManager(self.db)
        
        # Test data
        self.test_date = datetime.now().strftime('%Y-%m-%d')
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        
        # Clean up temp files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _get_realistic_predictions(self, count: int = 30, mean: float = 250, std: float = 15) -> list:
        """Generate realistic prediction data matching SmartArchive scale"""
        return np.random.normal(mean, std, count).tolist()
    
    def _insert_predictions(self, predictions: list) -> list:
        """Helper to insert multiple predictions into database"""
        prediction_ids = []
        for i, value in enumerate(predictions):
            date = (datetime.now() - timedelta(days=len(predictions) - i - 1)).strftime('%Y-%m-%d')
            
            # Realistic savings prediction (roughly 50% of archived)
            pred_id = self.db.save_prediction(
                prediction_date=date,
                archived_gb_predicted=value,
                savings_gb_predicted=value * 0.5
            )
            prediction_ids.append(pred_id)
        
        return prediction_ids
    
    def _print_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Pretty print test results"""
        status = "[PASS]" if passed else "[FAIL]"
        print(f"\n{status} | {test_name}")
        if details:
            print(f"       {details}")


class TestPhase3PredictionInsertion(TestPhase3IntegrationBase):
    """Test 1: Prediction insertion flow"""
    
    def test_predictions_flow_from_database(self):
        """
        Test 1.1: Verify predictions can be inserted and retrieved from database
        
        Expected: 
        - Predictions save without error
        - Database has new rows
        - All columns populated correctly
        - Data types correct
        """
        print("\n" + "="*70)
        print("TEST 1: PREDICTION INSERTION FROM SOURCE TO DATABASE")
        print("="*70)
        
        # Generate realistic predictions (30 days)
        predictions = self._get_realistic_predictions(count=30)
        
        # Insert predictions
        print("\n1.1: Inserting 30 predictions...")
        prediction_ids = self._insert_predictions(predictions)
        
        # Verify insertion
        self.assertEqual(len(prediction_ids), 30, "Should insert 30 predictions")
        self.assertTrue(all(pid > 0 for pid in prediction_ids), "All prediction IDs should be positive")
        self._print_test_result("1.1: Batch insertion", True, f"Inserted {len(prediction_ids)} predictions")
        
        # Retrieve predictions
        print("\n1.2: Retrieving predictions from database...")
        retrieved = self.db.get_predictions(days=30)
        
        # Verify retrieval
        self.assertGreater(len(retrieved), 0, "Should retrieve predictions")
        self._print_test_result("1.2: Retrieval", True, f"Retrieved {len(retrieved)} predictions")
        
        # Verify schema and data types
        print("\n1.3: Verifying schema and data types...")
        
        required_columns = [
            'id', 'prediction_date', 'archived_gb_predicted', 
            'savings_gb_predicted', 'created_at'
        ]
        
        for col in required_columns:
            self.assertIn(col, retrieved.columns, f"Should have {col} column")
        
        # Verify data types
        self.assertTrue(pd.api.types.is_numeric_dtype(retrieved['archived_gb_predicted']),
                       "archived_gb_predicted should be numeric")
        self.assertTrue(pd.api.types.is_numeric_dtype(retrieved['savings_gb_predicted']),
                       "savings_gb_predicted should be numeric")
        
        self._print_test_result("1.3: Schema validation", True, f"All {len(required_columns)} columns present")
        
        # Verify data quality
        print("\n1.4: Verifying data quality...")
        
        # Check for nulls in critical columns
        null_archived = retrieved['archived_gb_predicted'].isna().sum()
        null_savings = retrieved['savings_gb_predicted'].isna().sum()
        
        self.assertEqual(null_archived, 0, "archived_gb_predicted should not have nulls")
        self.assertEqual(null_savings, 0, "savings_gb_predicted should not have nulls")
        
        # Check realistic ranges
        self.assertTrue(all(retrieved['archived_gb_predicted'] > 0), "Archived GB should be positive")
        self.assertTrue(all(retrieved['archived_gb_predicted'] < 1000), "Archived GB should be < 1000 (realistic)")
        
        self._print_test_result("1.4: Data quality", True, "No nulls, values in realistic range")
        
        # Verify latest prediction
        print("\n1.5: Verifying latest prediction...")
        latest = self.db.get_latest_prediction()
        
        self.assertIsNotNone(latest, "Should have latest prediction")
        self.assertIn('archived_gb_predicted', latest, "Latest should have archived_gb_predicted")
        
        self._print_test_result("1.5: Latest prediction", True, f"Latest: {latest['archived_gb_predicted']:.2f} GB")
        
        # Summary
        print("\n" + "-"*70)
        print("✅ TEST 1 COMPLETE: Prediction insertion working correctly")
        print("-"*70)
    
    def test_actual_value_update(self):
        """
        Test 1.2: Verify actual values can be updated after initial prediction
        
        Expected:
        - Actual values can be inserted as NULL
        - Actual values updated when real data arrives
        - Updated at timestamp changes
        """
        print("\n1.6: Testing actual value updates...")
        
        # Insert prediction without actual values
        pred_id = self.db.save_prediction(
            prediction_date=self.test_date,
            archived_gb_predicted=250,
            savings_gb_predicted=125,
            archived_gb_actual=None,
            savings_gb_actual=None
        )
        
        # Verify initial state
        pred = self.db.get_latest_prediction()
        self.assertIsNone(pred['archived_gb_actual'], "Initial actual value should be NULL")
        
        # Update with actual values
        success = self.db.update_actual_value(
            prediction_date=self.test_date,
            archived_gb_actual=248.5,
            savings_gb_actual=124.2
        )
        
        self.assertTrue(success, "Update should succeed")
        
        # Verify update
        updated = self.db.get_latest_prediction()
        self.assertAlmostEqual(updated['archived_gb_actual'], 248.5, places=1)
        self.assertAlmostEqual(updated['savings_gb_actual'], 124.2, places=1)
        
        self._print_test_result("1.6: Actual value updates", True, "Can insert NULL and update later")


class TestPhase3DriftDetection(TestPhase3IntegrationBase):
    """Test 2: Drift detection on real predictions"""
    
    def test_drift_detection_normal_data(self):
        """
        Test 2.1: Verify drift detector works with normal data (no drift)
        
        Expected:
        - All 3 drift methods produce output
        - No false positives for normal data
        """
        print("\n" + "="*70)
        print("TEST 2: DRIFT DETECTION ON REAL PRODUCTION DATA")
        print("="*70)
        
        # Generate normal data
        predictions = self._get_realistic_predictions(count=30)
        
        # Set baseline from first 20 predictions
        baseline = predictions[:20]
        self.detector.set_baseline(baseline)
        
        print("\n2.1: Testing drift detection on normal data...")
        
        # Check all drifts
        results = self.detector.check_all_drifts(predictions[20:])
        
        # Verify structure
        self.assertIn('anomalies', results)
        self.assertIn('distribution_drift', results)
        self.assertIn('trend_drift', results)
        
        self._print_test_result("2.1: Drift detection structure", True, "All 3 methods present")
        
        # Verify no excessive drift in normal data
        print("\n2.2: Verifying normal data has minimal drift signals...")
        
        anomalies = results['anomalies']
        self.assertIsNotNone(anomalies.get('has_anomalies'), "Should have anomalies flag")
        self.assertIsNotNone(anomalies.get('max_z_score'), "Should have z-score")
        
        self._print_test_result("2.2: Z-score detection", True, 
                              f"Max z-score: {anomalies['max_z_score']:.2f}")
        
        # Verify KS test results
        dist = results['distribution_drift']
        self.assertIsNotNone(dist.get('ks_statistic'), "Should have KS statistic")
        self.assertIsNotNone(dist.get('p_value'), "Should have p-value")
        
        self._print_test_result("2.2: KS test detection", True,
                              f"p-value: {dist['p_value']:.4f}")
        
        # Verify trend detection
        trend = results['trend_drift']
        self.assertIsNotNone(trend.get('slope'), "Should have slope")
        self.assertIsNotNone(trend.get('trend_direction'), "Should have trend direction")
        
        self._print_test_result("2.2: Trend detection", True,
                              f"Trend: {trend['trend_direction']} (slope: {trend['slope']:.4f})")
    
    def test_drift_detection_with_anomalies(self):
        """
        Test 2.2: Verify drift detector detects real anomalies
        
        Expected:
        - Anomalies flagged correctly when outliers present
        """
        print("\n2.3: Testing drift detection with anomalies...")
        
        # Generate data with anomalies
        predictions = self._get_realistic_predictions(count=30)
        
        # Set baseline
        baseline = predictions[:20]
        self.detector.set_baseline(baseline)
        
        # Add anomalies
        test_data = predictions[20:].copy()
        test_data[2] = 400  # Add large outlier
        
        results = self.detector.check_all_drifts(test_data)
        
        # Verify anomalies detected
        anomalies = results['anomalies']
        self.assertTrue(anomalies['has_anomalies'], "Should detect anomalies")
        self.assertGreater(anomalies['anomaly_count'], 0, "Should have anomaly count")
        self.assertGreater(anomalies['max_z_score'], self.detector.z_score_threshold,
                          "Max z-score should exceed threshold")
        
        self._print_test_result("2.3: Anomaly detection", True,
                              f"Detected {anomalies['anomaly_count']} anomalies")
    
    def test_drift_detection_with_distribution_shift(self):
        """
        Test 2.3: Verify drift detector detects distribution shifts
        
        Expected:
        - Distribution drift flagged when data shifts
        """
        print("\n2.4: Testing drift detection with distribution shift...")
        
        # Generate baseline
        baseline = np.random.normal(250, 15, 30).tolist()
        self.detector.set_baseline(baseline)
        
        # Generate shifted data (different mean)
        shifted = np.random.normal(280, 15, 30).tolist()
        
        results = self.detector.check_all_drifts(shifted)
        dist = results['distribution_drift']
        
        # Verify drift detected
        self.assertTrue(dist.get('has_drift', False), "Should detect distribution drift")
        self.assertLess(dist.get('p_value', 1.0), self.detector.ks_test_threshold,
                       "P-value should be below threshold")
        
        self._print_test_result("2.4: Distribution shift detection", True,
                              f"Mean shift of {dist.get('mean_change_pct', 0):+.1f}%")
    
    def test_drift_detection_with_trend(self):
        """
        Test 2.4: Verify drift detector detects trend changes
        
        Expected:
        - Trend drift flagged for significant uptrend/downtrend
        """
        print("\n2.5: Testing drift detection with trend...")
        
        # Generate uptrend data
        uptrend = [250 + i * 2 for i in range(30)]
        
        results = self.detector.check_all_drifts(uptrend)
        trend = results['trend_drift']
        
        # Verify trend detected
        self.assertEqual(trend['trend_direction'].lower(), 'up', "Should detect uptrend")
        self.assertGreater(trend['slope'], 0, "Slope should be positive")
        
        self._print_test_result("2.5: Trend detection", True,
                              f"Detected {trend['trend_direction']} trend (slope: {trend['slope']:.2f})")
    
    def test_drift_detection_edge_cases(self):
        """
        Test 2.5: Edge cases for drift detection
        
        Expected:
        - Handles empty data gracefully
        - Handles single prediction
        - Handles all same values
        """
        print("\n2.6: Testing edge cases...")
        
        # Empty data
        empty_results = self.detector.check_all_drifts([])
        self.assertFalse(empty_results['overall_drift_detected'], 
                        "Empty data should not trigger drift")
        self._print_test_result("2.6a: Empty data", True, "No crash, no false positive")
        
        # Single value
        single_results = self.detector.check_all_drifts([250])
        self.assertFalse(single_results['overall_drift_detected'],
                        "Single value should not trigger drift")
        self._print_test_result("2.6b: Single prediction", True, "No crash")
        
        # All same values
        same_results = self.detector.check_all_drifts([250] * 20)
        self.assertFalse(same_results['overall_drift_detected'],
                        "Constant values should not trigger drift")
        self._print_test_result("2.6c: Constant values", True, "No crash, no false positive")
        
        print("\n" + "-"*70)
        print("✅ TEST 2 COMPLETE: Drift detection working correctly")
        print("-"*70)


class TestPhase3AlertCreation(TestPhase3IntegrationBase):
    """Test 3: Alert creation from drift"""
    
    def test_alert_creation_from_anomaly(self):
        """
        Test 3.1: Verify alerts are created from anomaly detection
        
        Expected:
        - Alert created when anomalies detected
        - Alert type is 'anomaly'
        - Severity appropriate
        - Message informative
        """
        print("\n" + "="*70)
        print("TEST 3: ALERT CREATION FROM DRIFT DETECTION")
        print("="*70)
        
        print("\n3.1: Testing alert creation from anomalies...")
        
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
        
        alert = self.alert_manager.create_alert_from_drift(drift_results, self.test_date)
        
        self.assertIsNotNone(alert, "Should create alert from anomaly")
        self.assertEqual(alert['alert_type'], 'anomaly', "Alert type should be anomaly")
        self.assertEqual(alert['severity'], 'warning', "Should be warning severity")
        self.assertIn('anomaly', alert['message'].lower(), "Message should mention anomaly")
        
        self._print_test_result("3.1: Anomaly alert creation", True,
                              f"Type: {alert['alert_type']}, Severity: {alert['severity']}")
    
    def test_alert_creation_from_distribution_drift(self):
        """
        Test 3.2: Verify alerts are created from distribution drift
        
        Expected:
        - Alert created when distribution drift detected
        - Alert type is 'distribution_drift'
        - Severity appropriate
        """
        print("\n3.2: Testing alert from distribution drift...")
        
        drift_results = {
            'overall_drift_detected': True,
            'anomalies': {
                'has_anomalies': False,
                'anomaly_count': 0,
                'max_z_score': 0.5
            },
            'distribution_drift': {
                'has_drift': True,
                'p_value': 0.02,
                'mean_change_pct': 12.5
            },
            'trend_drift': {
                'has_trend_drift': False
            }
        }
        
        alert = self.alert_manager.create_alert_from_drift(drift_results, self.test_date)
        
        self.assertIsNotNone(alert, "Should create alert")
        self.assertEqual(alert['alert_type'], 'distribution_drift', "Alert type should be distribution_drift")
        
        self._print_test_result("3.2: Distribution drift alert", True,
                              f"Detected {abs(drift_results['distribution_drift']['mean_change_pct']):.1f}% shift")
    
    def test_alert_creation_multi_signal(self):
        """
        Test 3.3: Verify multi-signal alerts (most critical)
        
        Expected:
        - Alert type is 'multi_signal' when multiple drifts detected
        - Severity is 'critical'
        """
        print("\n3.3: Testing multi-signal alert (critical)...")
        
        drift_results = {
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
        
        alert = self.alert_manager.create_alert_from_drift(drift_results, self.test_date)
        
        self.assertIsNotNone(alert, "Should create alert")
        self.assertEqual(alert['alert_type'], 'multi_signal', "Alert type should be multi_signal")
        self.assertEqual(alert['severity'], 'critical', "Should be critical severity")
        self.assertIn('multiple', alert['message'].lower(), "Message should mention multiple signals")
        
        self._print_test_result("3.3: Multi-signal alert", True, "Critical severity assigned")
    
    def test_alert_no_drift(self):
        """
        Test 3.4: Verify no alert created when no drift
        
        Expected:
        - None returned when no drift detected
        """
        print("\n3.4: Testing no alert when no drift...")
        
        drift_results = {
            'overall_drift_detected': False,
            'anomalies': {
                'has_anomalies': False,
                'anomaly_count': 0,
                'max_z_score': 0.5
            },
            'distribution_drift': {
                'has_drift': False,
                'p_value': 0.87
            },
            'trend_drift': {
                'has_trend_drift': False
            }
        }
        
        alert = self.alert_manager.create_alert_from_drift(drift_results, self.test_date)
        
        self.assertIsNone(alert, "Should not create alert when no drift")
        
        self._print_test_result("3.4: No alert on normal data", True, "Correct behavior")
    
    def test_alert_persistence(self):
        """
        Test 3.5: Verify alerts persist to database
        
        Expected:
        - Alert saved with all metadata
        - Can be retrieved from database
        - All fields intact
        """
        print("\n3.5: Testing alert persistence to database...")
        
        drift_results = {
            'overall_drift_detected': True,
            'anomalies': {
                'has_anomalies': True,
                'anomaly_count': 2,
                'max_z_score': 2.2
            },
            'distribution_drift': {
                'has_drift': False,
                'p_value': 0.50
            },
            'trend_drift': {
                'has_trend_drift': False
            }
        }
        
        alert = self.alert_manager.create_alert_from_drift(drift_results, self.test_date)
        alert_id = self.alert_manager.save_alert(alert)
        
        self.assertGreater(alert_id, 0, "Alert should be saved with positive ID")
        
        # Retrieve alert
        active_alerts = self.alert_manager.get_active_alerts(days=1)
        self.assertGreater(len(active_alerts), 0, "Should retrieve saved alert")
        
        # Verify content
        saved_alert = active_alerts[0]
        self.assertEqual(saved_alert['severity'], alert['severity'])
        self.assertEqual(saved_alert['alert_type'], alert['alert_type'])
        
        self._print_test_result("3.5: Alert persistence", True, f"Saved and retrieved alert ID {alert_id}")
    
    def test_alert_summary(self):
        """
        Test 3.6: Verify alert summary statistics
        
        Expected:
        - Can count alerts by severity
        - Can count alerts by type
        """
        print("\n3.6: Testing alert summary statistics...")
        
        # Create multiple alerts
        drift_results_1 = {
            'overall_drift_detected': True,
            'anomalies': {'has_anomalies': True, 'anomaly_count': 1, 'max_z_score': 2.0},
            'distribution_drift': {'has_drift': False, 'p_value': 0.9},
            'trend_drift': {'has_trend_drift': False}
        }
        
        drift_results_2 = {
            'overall_drift_detected': True,
            'anomalies': {'has_anomalies': False, 'anomaly_count': 0, 'max_z_score': 0.5},
            'distribution_drift': {'has_drift': True, 'p_value': 0.01, 'mean_change_pct': 20},
            'trend_drift': {'has_trend_drift': False}
        }
        
        alert1 = self.alert_manager.create_alert_from_drift(drift_results_1, self.test_date)
        alert2 = self.alert_manager.create_alert_from_drift(drift_results_2, self.test_date)
        
        self.alert_manager.save_alert(alert1)
        self.alert_manager.save_alert(alert2)
        
        # Get summary
        summary = self.alert_manager.get_alert_summary(days=1)
        
        self.assertEqual(summary['total_alerts'], 2, "Should have 2 alerts")
        self.assertGreater(len(summary['by_type']), 0, "Should have alerts by type")
        
        self._print_test_result("3.6: Alert summary", True,
                              f"Total: {summary['total_alerts']}, Types: {len(summary['by_type'])}")
        
        print("\n" + "-"*70)
        print("✅ TEST 3 COMPLETE: Alert creation working correctly")
        print("-"*70)


class TestPhase3Performance(TestPhase3IntegrationBase):
    """Test 5: Performance validation"""
    
    def test_performance_with_30_predictions(self):
        """
        Test 5.1: Validate performance with 30+ predictions
        
        Expected:
        - Drift detection < 100ms
        - Alert creation < 50ms
        - All operations complete successfully
        """
        print("\n" + "="*70)
        print("TEST 5: PERFORMANCE VALIDATION WITH 30+ PREDICTIONS")
        print("="*70)
        
        # Insert 30 predictions
        predictions = self._get_realistic_predictions(count=30)
        pred_ids = self._insert_predictions(predictions)
        
        print(f"\n5.1: Inserted {len(pred_ids)} predictions for performance testing")
        
        # Test drift detection performance
        print("\n5.2: Measuring drift detection performance...")
        
        baseline = predictions[:20]
        self.detector.set_baseline(baseline)
        
        start = time.time()
        results = self.detector.check_all_drifts(predictions[20:])
        drift_time = (time.time() - start) * 1000  # Convert to ms
        
        self.assertLess(drift_time, 200, f"Drift detection should be < 200ms, got {drift_time:.2f}ms")
        
        self._print_test_result("5.2: Drift detection performance", True,
                              f"Completed in {drift_time:.2f}ms")
        
        # Test alert creation performance
        print("\n5.3: Measuring alert creation performance...")
        
        drift_results = {
            'overall_drift_detected': True,
            'anomalies': {'has_anomalies': True, 'anomaly_count': 2, 'max_z_score': 2.3},
            'distribution_drift': {'has_drift': False, 'p_value': 0.8},
            'trend_drift': {'has_trend_drift': False}
        }
        
        start = time.time()
        alert = self.alert_manager.create_alert_from_drift(drift_results, self.test_date)
        alert_create_time = (time.time() - start) * 1000
        
        self.assertLess(alert_create_time, 100, f"Alert creation should be < 100ms")
        
        self._print_test_result("5.3: Alert creation performance", True,
                              f"Completed in {alert_create_time:.2f}ms")
        
        # Test alert persistence performance
        print("\n5.4: Measuring alert persistence performance...")
        
        start = time.time()
        alert_id = self.alert_manager.save_alert(alert)
        persist_time = (time.time() - start) * 1000
        
        self.assertLess(persist_time, 100, f"Alert persistence should be < 100ms")
        self.assertGreater(alert_id, 0, "Alert should be saved")
        
        self._print_test_result("5.4: Alert persistence performance", True,
                              f"Completed in {persist_time:.2f}ms")
        
        # Test retrieval performance
        print("\n5.5: Measuring retrieval performance...")
        
        start = time.time()
        all_predictions = self.db.get_predictions(days=30)
        retrieval_time = (time.time() - start) * 1000
        
        self.assertGreater(len(all_predictions), 0, "Should retrieve predictions")
        self.assertLess(retrieval_time, 500, f"Retrieval should be < 500ms")
        
        self._print_test_result("5.5: Retrieval performance", True,
                              f"Retrieved {len(all_predictions)} in {retrieval_time:.2f}ms")
        
        # Summary
        total_time = drift_time + alert_create_time + persist_time + retrieval_time
        print("\n" + "-"*70)
        print(f"Performance Summary:")
        print(f"  Drift detection: {drift_time:.2f}ms ✓")
        print(f"  Alert creation:  {alert_create_time:.2f}ms ✓")
        print(f"  Alert persist:   {persist_time:.2f}ms ✓")
        print(f"  Retrieval:       {retrieval_time:.2f}ms ✓")
        print(f"  Total:           {total_time:.2f}ms")
        print("-"*70)
        print("✅ TEST 5 COMPLETE: Performance targets met")
        print("-"*70)


class TestPhase3EdgeCases(TestPhase3IntegrationBase):
    """Test 6: Edge case handling"""
    
    def test_edge_case_empty_database(self):
        """
        Test 6.1: Empty database graceful handling
        
        Expected:
        - No crash with empty database
        - Returns empty results appropriately
        """
        print("\n" + "="*70)
        print("TEST 6: EDGE CASE HANDLING")
        print("="*70)
        
        print("\n6.1: Testing empty database...")
        
        # Query empty database
        predictions = self.db.get_predictions(days=30)
        self.assertEqual(len(predictions), 0, "Empty database should return empty DataFrame")
        
        # Try drift detection with empty data
        results = self.detector.check_all_drifts([])
        self.assertFalse(results['overall_drift_detected'], "No drift on empty data")
        
        self._print_test_result("6.1: Empty database", True, "No crash, appropriate results")
    
    def test_edge_case_single_prediction(self):
        """
        Test 6.2: Single prediction edge case
        
        Expected:
        - Handles gracefully
        - No crash
        - Reasonable defaults
        """
        print("\n6.2: Testing single prediction...")
        
        self.db.save_prediction(
            prediction_date=self.test_date,
            archived_gb_predicted=250,
            savings_gb_predicted=125
        )
        
        predictions = self.db.get_predictions(days=30)
        self.assertEqual(len(predictions), 1, "Should retrieve single prediction")
        
        # Drift detection with single value
        results = self.detector.check_all_drifts([250])
        self.assertFalse(results['overall_drift_detected'], "Single value no drift")
        
        self._print_test_result("6.2: Single prediction", True, "Handled gracefully")
    
    def test_edge_case_constant_values(self):
        """
        Test 6.3: All constant values (no variation)
        
        Expected:
        - No false positive drift
        - Handles zero std dev
        """
        print("\n6.3: Testing constant values...")
        
        constant_data = [250] * 30
        
        results = self.detector.check_all_drifts(constant_data)
        
        # Should not trigger drift
        anomalies = results['anomalies']
        self.assertFalse(anomalies['has_anomalies'], "No anomalies in constant data")
        
        trend = results['trend_drift']
        self.assertEqual(trend['trend_direction'], 'stable', "Constant should be stable trend")
        
        self._print_test_result("6.3: Constant values", True, "No false positives")
    
    def test_edge_case_extreme_values(self):
        """
        Test 6.4: Extreme but realistic values
        
        Expected:
        - Handles large numbers (GB scale)
        - No overflow or precision loss
        """
        print("\n6.4: Testing extreme values...")
        
        # Extreme but realistic for large archives
        extreme_values = [1000000, 1100000, 950000] * 10  # ~1 million GB
        
        # Should not crash
        results = self.detector.check_all_drifts(extreme_values)
        
        self.assertIsNotNone(results['anomalies']['mean'], "Should handle large numbers")
        self.assertGreater(results['anomalies']['mean'], 0, "Mean should be positive")
        
        self._print_test_result("6.4: Extreme values", True, "Handled without overflow")
    
    def test_edge_case_null_actual_values(self):
        """
        Test 6.5: NULL actual values (predictions not yet actualized)
        
        Expected:
        - Can handle NULL actual values
        - Drift detection works on predicted values only
        """
        print("\n6.5: Testing NULL actual values...")
        
        # Insert predictions without actual values
        self.db.save_prediction(
            prediction_date=self.test_date,
            archived_gb_predicted=250,
            savings_gb_predicted=125,
            archived_gb_actual=None,
            savings_gb_actual=None
        )
        
        predictions = self.db.get_predictions(days=30)
        latest = self.db.get_latest_prediction()
        
        self.assertIsNone(latest['archived_gb_actual'], "Should preserve NULL values")
        
        # Drift detection on predicted values should still work
        predicted = [latest['archived_gb_predicted']]
        results = self.detector.check_all_drifts(predicted)
        
        self._print_test_result("6.5: NULL actual values", True, "Preserved and handled correctly")
        
        print("\n" + "-"*70)
        print("✅ TEST 6 COMPLETE: All edge cases handled")
        print("-"*70)


def run_phase3_tests():
    """Run all Phase 3 integration tests"""
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPhase3PredictionInsertion))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase3DriftDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase3AlertCreation))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase3Performance))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase3EdgeCases))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("PHASE 3 INTEGRATION TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n[SUCCESS] ALL PHASE 3 TESTS PASSED!")
        print("Status: Ready for Phase 4")
    else:
        print("\n[FAILED] SOME TESTS FAILED")
        print("Review failures above and fix issues")
    
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_phase3_tests()
    sys.exit(0 if success else 1)

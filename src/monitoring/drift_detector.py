"""
Drift Detection Module

Implements statistical methods to detect data drift and prediction drift in the model.
Uses z-score and Kolmogorov-Smirnov test for drift detection.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from scipy import stats
from datetime import datetime


class DriftDetector:
    """
    Detects statistical drift in predictions and input data.
    Helps identify when model performance may be degrading.
    """
    
    def __init__(
        self,
        z_score_threshold: float = 2.0,
        ks_test_threshold: float = 0.05,
        min_samples: int = 10
    ):
        """
        Initialize drift detector with thresholds
        
        Args:
            z_score_threshold: Z-score threshold for anomaly detection (default: 2.0 = ~95% confidence)
            ks_test_threshold: P-value threshold for Kolmogorov-Smirnov test (default: 0.05 = 95% confidence)
            min_samples: Minimum samples needed for drift detection (default: 10)
        """
        self.z_score_threshold = z_score_threshold
        self.ks_test_threshold = ks_test_threshold
        self.min_samples = min_samples
        self.baseline_mean = None
        self.baseline_std = None
    
    def set_baseline(self, values: List[float]) -> bool:
        """
        Set baseline statistics for drift comparison
        
        Args:
            values: List of baseline values (e.g., first 30 days of predictions)
        
        Returns:
            True if baseline set successfully, False if insufficient data
        """
        if len(values) < self.min_samples:
            print(f"Warning: Need at least {self.min_samples} samples for baseline. Got {len(values)}")
            return False
        
        self.baseline_mean = np.mean(values)
        self.baseline_std = np.std(values)
        
        if self.baseline_std == 0:
            print("Warning: Baseline standard deviation is zero. Drift detection may not work properly.")
        
        return True
    
    def detect_anomalies_zscore(
        self,
        values: List[float],
        use_baseline: bool = True
    ) -> Dict:
        """
        Detect anomalies using Z-score method
        
        Works by:
        1. Calculate z-score for each value: (value - mean) / std
        2. Flag values with |z-score| > threshold as anomalies
        
        Args:
            values: List of values to check for anomalies
            use_baseline: If True, use set baseline. If False, calculate from values.
        
        Returns:
            Dictionary with detection results:
            {
                'has_anomalies': bool,
                'anomaly_count': int,
                'anomaly_indices': List[int],
                'anomaly_values': List[float],
                'z_scores': List[float],
                'max_z_score': float,
                'mean': float,
                'std': float,
                'threshold': float
            }
        """
        if len(values) < 1:
            return {
                'has_anomalies': False,
                'anomaly_count': 0,
                'anomaly_indices': [],
                'anomaly_values': [],
                'z_scores': [],
                'max_z_score': 0,
                'mean': 0,
                'std': 0,
                'threshold': self.z_score_threshold
            }
        
        # Calculate statistics
        if use_baseline and self.baseline_mean is not None:
            mean = self.baseline_mean
            std = self.baseline_std
        else:
            mean = np.mean(values)
            std = np.std(values)
        
        # Handle case where std is 0
        if std == 0:
            std = 1e-10  # Avoid division by zero
        
        # Calculate z-scores
        z_scores = np.abs((np.array(values) - mean) / std)
        
        # Find anomalies
        anomalies = z_scores > self.z_score_threshold
        anomaly_indices = np.where(anomalies)[0].tolist()
        anomaly_values = [values[i] for i in anomaly_indices]
        
        return {
            'has_anomalies': bool(np.any(anomalies)),
            'anomaly_count': int(np.sum(anomalies)),
            'anomaly_indices': anomaly_indices,
            'anomaly_values': anomaly_values,
            'z_scores': z_scores.tolist(),
            'max_z_score': float(np.max(z_scores)) if len(z_scores) > 0 else 0,
            'mean': float(mean),
            'std': float(std),
            'threshold': self.z_score_threshold
        }
    
    def detect_drift_ks_test(
        self,
        current_values: List[float],
        baseline_values: Optional[List[float]] = None
    ) -> Dict:
        """
        Detect distribution drift using Kolmogorov-Smirnov test
        
        Works by:
        1. Compare current data distribution to baseline
        2. KS test produces p-value: prob. that distributions are same
        3. Low p-value = distributions are different = drift detected
        
        Args:
            current_values: List of current values to test
            baseline_values: List of baseline values (optional, uses set baseline if not provided)
        
        Returns:
            Dictionary with drift detection results:
            {
                'has_drift': bool,
                'ks_statistic': float,
                'p_value': float,
                'threshold': float,
                'current_mean': float,
                'baseline_mean': float,
                'mean_change_pct': float
            }
        """
        if len(current_values) < self.min_samples:
            return {
                'has_drift': False,
                'ks_statistic': 0,
                'p_value': 1.0,
                'threshold': self.ks_test_threshold,
                'current_mean': np.mean(current_values) if current_values else 0,
                'baseline_mean': 0,
                'mean_change_pct': 0,
                'error': f'Insufficient samples: {len(current_values)} < {self.min_samples}'
            }
        
        # Use provided baseline or set baseline
        if baseline_values is None:
            if self.baseline_mean is None:
                return {
                    'has_drift': False,
                    'ks_statistic': 0,
                    'p_value': 1.0,
                    'threshold': self.ks_test_threshold,
                    'current_mean': np.mean(current_values),
                    'baseline_mean': 0,
                    'mean_change_pct': 0,
                    'error': 'No baseline set for comparison'
                }
            baseline_values = np.random.normal(self.baseline_mean, self.baseline_std, self.min_samples)
        
        # Perform KS test
        ks_stat, p_value = stats.ks_2samp(current_values, baseline_values)
        
        current_mean = np.mean(current_values)
        baseline_mean = np.mean(baseline_values)
        mean_change_pct = ((current_mean - baseline_mean) / baseline_mean * 100) if baseline_mean != 0 else 0
        
        return {
            'has_drift': bool(p_value < self.ks_test_threshold),
            'ks_statistic': float(ks_stat),
            'p_value': float(p_value),
            'threshold': self.ks_test_threshold,
            'current_mean': float(current_mean),
            'baseline_mean': float(baseline_mean),
            'mean_change_pct': float(mean_change_pct)
        }
    
    def detect_trend_drift(
        self,
        values: List[float],
        window_size: int = 7
    ) -> Dict:
        """
        Detect trend drift by comparing recent vs older values
        
        Works by:
        1. Split data into two halves (recent vs older)
        2. Compare means of each half
        3. Large difference = trend drift (model output changing over time)
        
        Args:
            values: List of values to analyze
            window_size: Size of rolling window for trend (default: 7)
        
        Returns:
            Dictionary with trend drift results:
            {
                'has_trend_drift': bool,
                'recent_mean': float,
                'older_mean': float,
                'trend_direction': str ('up', 'down', 'stable'),
                'trend_change_pct': float,
                'slope': float
            }
        """
        if len(values) < window_size:
            return {
                'has_trend_drift': False,
                'recent_mean': 0,
                'older_mean': 0,
                'trend_direction': 'unknown',
                'trend_change_pct': 0,
                'slope': 0,
                'error': f'Insufficient samples: {len(values)} < {window_size}'
            }
        
        # Split into recent and older
        split_point = len(values) - window_size
        older_values = values[:split_point]
        recent_values = values[split_point:]
        
        older_mean = np.mean(older_values)
        recent_mean = np.mean(recent_values)
        
        # Calculate change percentage
        change_pct = ((recent_mean - older_mean) / older_mean * 100) if older_mean != 0 else 0
        
        # Determine trend direction
        if abs(change_pct) < 5:
            trend_direction = 'stable'
            has_drift = False
        else:
            trend_direction = 'up' if change_pct > 0 else 'down'
            has_drift = abs(change_pct) > 10  # Drift if change > 10%
        
        # Calculate simple linear trend (slope)
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        return {
            'has_trend_drift': has_drift,
            'recent_mean': float(recent_mean),
            'older_mean': float(older_mean),
            'trend_direction': trend_direction,
            'trend_change_pct': float(change_pct),
            'slope': float(slope)
        }
    
    def check_all_drifts(
        self,
        values: List[float],
        baseline_values: Optional[List[float]] = None
    ) -> Dict:
        """
        Run all drift detection methods and return comprehensive results
        
        Args:
            values: List of values to analyze
            baseline_values: Optional baseline for KS test
        
        Returns:
            Dictionary with all drift detection results
        """
        anom_result = self.detect_anomalies_zscore(values)
        dist_result = self.detect_drift_ks_test(values, baseline_values)
        trend_result = self.detect_trend_drift(values)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'anomalies': anom_result,
            'distribution_drift': dist_result,
            'trend_drift': trend_result,
            'overall_drift_detected': bool(
                anom_result['has_anomalies'] or
                dist_result['has_drift'] or
                trend_result['has_trend_drift']
            )
        }
    
    def get_drift_summary(self, drift_results: Dict) -> str:
        """
        Generate human-readable summary of drift detection results
        
        Args:
            drift_results: Results from check_all_drifts()
        
        Returns:
            Formatted summary string
        """
        summary = []
        
        if drift_results['overall_drift_detected']:
            summary.append("🔴 DRIFT DETECTED")
        else:
            summary.append("✅ NO DRIFT")
        
        # Anomalies
        anom = drift_results['anomalies']
        if anom['has_anomalies']:
            summary.append(f"  • {anom['anomaly_count']} anomalies (z-score > {anom['threshold']})")
            summary.append(f"    Max z-score: {anom['max_z_score']:.2f}")
        
        # Distribution drift
        dist = drift_results['distribution_drift']
        if 'error' not in dist:
            if dist['has_drift']:
                summary.append(f"  • Distribution drift detected (p={dist['p_value']:.4f})")
                summary.append(f"    Mean change: {dist['mean_change_pct']:.1f}%")
        
        # Trend drift
        trend = drift_results['trend_drift']
        if 'error' not in trend:
            summary.append(f"  • Trend: {trend['trend_direction'].upper()} ({trend['trend_change_pct']:+.1f}%)")
            if trend['has_trend_drift']:
                summary.append(f"    ⚠️  Significant trend change detected")
        
        return "\n".join(summary)


if __name__ == "__main__":
    """Test drift detector functionality"""
    import json
    
    print("Testing DriftDetector...")
    print("=" * 60)
    
    # Initialize detector
    detector = DriftDetector(z_score_threshold=2.0, ks_test_threshold=0.05)
    
    # Test 1: Set baseline
    print("\n✓ Test 1: Setting baseline...")
    baseline = np.random.normal(250, 15, 30).tolist()
    success = detector.set_baseline(baseline)
    print(f"  Baseline set: {success}")
    print(f"  Baseline mean: {detector.baseline_mean:.2f}")
    print(f"  Baseline std: {detector.baseline_std:.2f}")
    
    # Test 2: Normal data (no drift)
    print("\n✓ Test 2: Testing normal data (should be no drift)...")
    normal_data = np.random.normal(250, 15, 30).tolist()
    anomalies = detector.detect_anomalies_zscore(normal_data)
    print(f"  Anomalies detected: {anomalies['has_anomalies']}")
    print(f"  Anomaly count: {anomalies['anomaly_count']}")
    print(f"  Max z-score: {anomalies['max_z_score']:.2f}")
    
    # Test 3: Data with anomaly
    print("\n✓ Test 3: Testing data with anomaly...")
    data_with_anomaly = normal_data.copy()
    data_with_anomaly[5] = 350  # Insert outlier
    anomalies = detector.detect_anomalies_zscore(data_with_anomaly)
    print(f"  Anomalies detected: {anomalies['has_anomalies']}")
    print(f"  Anomaly count: {anomalies['anomaly_count']}")
    print(f"  Anomaly indices: {anomalies['anomaly_indices']}")
    print(f"  Max z-score: {anomalies['max_z_score']:.2f}")
    
    # Test 4: KS test for distribution drift
    print("\n✓ Test 4: Testing KS test (normal data)...")
    drift = detector.detect_drift_ks_test(normal_data)
    print(f"  Drift detected: {drift['has_drift']}")
    print(f"  KS statistic: {drift['ks_statistic']:.4f}")
    print(f"  P-value: {drift['p_value']:.4f}")
    
    # Test 5: KS test with shifted data (drift)
    print("\n✓ Test 5: Testing KS test (shifted data - should detect drift)...")
    shifted_data = np.random.normal(280, 15, 30).tolist()  # Shifted mean
    drift = detector.detect_drift_ks_test(shifted_data)
    print(f"  Drift detected: {drift['has_drift']}")
    print(f"  KS statistic: {drift['ks_statistic']:.4f}")
    print(f"  P-value: {drift['p_value']:.4f}")
    print(f"  Current mean: {drift['current_mean']:.2f}")
    print(f"  Baseline mean: {drift['baseline_mean']:.2f}")
    print(f"  Mean change: {drift['mean_change_pct']:+.1f}%")
    
    # Test 6: Trend drift
    print("\n✓ Test 6: Testing trend drift (upward trend)...")
    uptrend_data = [250 + i * 1.5 for i in range(30)]  # Upward trend
    trend = detector.detect_trend_drift(uptrend_data)
    print(f"  Trend drift detected: {trend['has_trend_drift']}")
    print(f"  Trend direction: {trend['trend_direction']}")
    print(f"  Trend change: {trend['trend_change_pct']:+.1f}%")
    print(f"  Slope: {trend['slope']:.4f}")
    
    # Test 7: Comprehensive drift check
    print("\n✓ Test 7: Comprehensive drift check...")
    all_results = detector.check_all_drifts(shifted_data)
    summary = detector.get_drift_summary(all_results)
    print(f"\n{summary}")
    
    # Test 8: Multiple drift signals
    print("\n✓ Test 8: Testing multiple drift signals...")
    multi_drift_data = shifted_data.copy()
    multi_drift_data[5] = 400  # Add anomaly
    all_results = detector.check_all_drifts(multi_drift_data)
    summary = detector.get_drift_summary(all_results)
    print(f"\n{summary}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")

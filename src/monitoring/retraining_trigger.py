"""
Retraining Trigger Module

Evaluates conditions to determine if model retraining should be initiated.
Checks: feedback count, drift detection score, and accuracy drops.
"""

import pandas as pd
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta


class RetaininingTrigger:
    """Evaluates conditions for triggering model retraining"""
    
    def __init__(
        self,
        feedback_threshold: int = 50,
        drift_threshold: float = 0.3,
        accuracy_drop_threshold: float = 0.05,
        lookback_days: int = 7
    ):
        """
        Initialize retraining trigger
        
        Args:
            feedback_threshold: Minimum feedback count to trigger retraining
            drift_threshold: Minimum drift score to trigger retraining
            accuracy_drop_threshold: Minimum accuracy drop % to trigger retraining
            lookback_days: Number of days to look back for evaluation
        """
        self.feedback_threshold = feedback_threshold
        self.drift_threshold = drift_threshold
        self.accuracy_drop_threshold = accuracy_drop_threshold
        self.lookback_days = lookback_days
    
    def evaluate(
        self,
        feedback_count: int,
        drift_score: float,
        recent_accuracy: float,
        baseline_accuracy: float
    ) -> Dict:
        """
        Evaluate if retraining should be triggered
        
        Args:
            feedback_count: Number of feedback records collected
            drift_score: Drift detection score (0-1)
            recent_accuracy: Current model accuracy
            baseline_accuracy: Original model accuracy
        
        Returns:
            Dictionary with evaluation results:
            {
                'should_retrain': bool,
                'reason': str,
                'confidence': float,
                'metrics': dict,
                'trigger_details': dict
            }
        """
        
        # Calculate metrics
        accuracy_drop = 1 - (recent_accuracy / baseline_accuracy) if baseline_accuracy > 0 else 0
        
        # Evaluate each condition
        condition_feedback = feedback_count >= self.feedback_threshold
        condition_drift = drift_score >= self.drift_threshold
        condition_accuracy = accuracy_drop >= self.accuracy_drop_threshold
        
        # Trigger if majority of conditions are met (2 out of 3)
        conditions_met = sum([condition_feedback, condition_drift, condition_accuracy])
        should_retrain = conditions_met >= 2
        
        # Calculate confidence score (0-1)
        confidence = self._calculate_confidence(
            feedback_count,
            drift_score,
            accuracy_drop
        )
        
        # Build reason string
        reasons = []
        if condition_feedback:
            reasons.append(f"Sufficient feedback: {feedback_count}/{self.feedback_threshold}")
        if condition_drift:
            reasons.append(f"Drift detected: {drift_score:.3f}/{self.drift_threshold}")
        if condition_accuracy:
            reasons.append(f"Accuracy drop: {accuracy_drop*100:.1f}%/{self.accuracy_drop_threshold*100:.1f}%")
        
        if not reasons:
            reasons.append("No trigger conditions met")
        
        reason = " + ".join(reasons) if should_retrain else " (all conditions: " + ", ".join(reasons) + ")"
        
        return {
            'should_retrain': should_retrain,
            'reason': f"Retraining {'triggered' if should_retrain else 'not triggered'}: {reason}",
            'confidence': confidence,
            'conditions_met': conditions_met,
            'metrics': {
                'feedback_count': feedback_count,
                'drift_score': drift_score,
                'accuracy_drop': accuracy_drop,
                'recent_accuracy': recent_accuracy,
                'baseline_accuracy': baseline_accuracy
            },
            'trigger_details': {
                'condition_feedback': condition_feedback,
                'condition_drift': condition_drift,
                'condition_accuracy': condition_accuracy,
                'feedback_threshold': self.feedback_threshold,
                'drift_threshold': self.drift_threshold,
                'accuracy_drop_threshold': self.accuracy_drop_threshold
            }
        }
    
    def _calculate_confidence(
        self,
        feedback_count: int,
        drift_score: float,
        accuracy_drop: float
    ) -> float:
        """
        Calculate confidence score for retraining decision
        
        Args:
            feedback_count: Number of feedback records
            drift_score: Drift score (0-1)
            accuracy_drop: Accuracy drop (0-1)
        
        Returns:
            Confidence score (0-1)
        """
        # Normalize metrics to 0-1 range
        feedback_score = min(feedback_count / self.feedback_threshold, 1.0)
        drift_score_norm = min(drift_score / self.drift_threshold, 1.0)
        accuracy_score = min(accuracy_drop / self.accuracy_drop_threshold, 1.0)
        
        # Average the normalized scores
        confidence = (feedback_score + drift_score_norm + accuracy_score) / 3
        
        return min(confidence, 1.0)
    
    def get_recommendations(self, evaluation: Dict) -> Dict:
        """
        Get recommendations based on evaluation
        
        Args:
            evaluation: Result from evaluate()
        
        Returns:
            Dictionary with recommendations
        """
        confidence = evaluation['confidence']
        metrics = evaluation['metrics']
        
        recommendations = {
            'action': 'retrain' if evaluation['should_retrain'] else 'monitor',
            'urgency': self._calculate_urgency(confidence),
            'next_check': self._estimate_next_check(metrics),
            'data_needed': self._estimate_data_needed(metrics),
            'estimated_impact': self._estimate_impact(metrics)
        }
        
        return recommendations
    
    def _calculate_urgency(self, confidence: float) -> str:
        """Calculate urgency level based on confidence"""
        if confidence >= 0.8:
            return 'high'
        elif confidence >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_next_check(self, metrics: Dict) -> str:
        """Estimate when next evaluation check should occur"""
        if metrics['drift_score'] > 0.5:
            return '2 hours'
        elif metrics['feedback_count'] > 20:
            return '4 hours'
        else:
            return '12 hours'
    
    def _estimate_data_needed(self, metrics: Dict) -> Dict:
        """Estimate how much more data is needed"""
        feedback_gap = max(self.feedback_threshold - metrics['feedback_count'], 0)
        
        return {
            'more_feedback_needed': feedback_gap,
            'feedback_collection_rate': '~10 per day (estimated)',
            'days_to_threshold': max(1, (feedback_gap + 9) // 10)
        }
    
    def _estimate_impact(self, metrics: Dict) -> Dict:
        """Estimate expected impact of retraining"""
        accuracy_drop = metrics['accuracy_drop']
        drift_score = metrics['drift_score']
        
        # Rough estimate: retraining typically recovers 30-50% of accuracy drop
        potential_recovery = accuracy_drop * 0.4
        
        return {
            'estimated_accuracy_improvement': f"+{potential_recovery*100:.1f}%",
            'confidence_of_improvement': 'moderate' if drift_score > 0.3 else 'low',
            'training_time_estimate': '15-30 minutes'
        }


class RetainingTriggerManager:
    """Manages retraining trigger evaluation with database integration"""
    
    def __init__(self, feedback_db=None, predictions_db=None, drift_detector=None):
        """
        Initialize trigger manager
        
        Args:
            feedback_db: FeedbackDB instance
            predictions_db: PredictionsDB instance
            drift_detector: DriftDetector instance
        """
        self.feedback_db = feedback_db
        self.predictions_db = predictions_db
        self.drift_detector = drift_detector
        self.trigger = RetaininingTrigger()
    
    def check_retraining_conditions(self) -> Dict:
        """
        Check all retraining conditions using current data
        
        Returns:
            Dictionary with evaluation results
        """
        if not self.feedback_db or not self.predictions_db:
            return {
                'should_retrain': False,
                'reason': 'Database connections not configured',
                'error': True
            }
        
        # Get metrics
        feedback_count = self.feedback_db.get_feedback_count(days=7)
        feedback_metrics = self.feedback_db.get_feedback_accuracy(days=30)
        
        # Get drift score
        drift_score = 0.0
        if self.drift_detector:
            try:
                archived_list, savings_list = self.predictions_db.get_recent_predictions_for_drift()
                if len(archived_list) >= 10:  # Need at least 10 samples for drift detection
                    # Use KS test for drift detection
                    drift_result = self.drift_detector.detect_drift_ks_test(archived_list)
                    # Extract drift score from result
                    if drift_result.get('has_drift'):
                        drift_score = drift_result.get('p_value', 0.0)
                        # Invert p-value so higher score = more drift (for consistency)
                        drift_score = 1.0 - drift_score if drift_score <= 1.0 else 0.0
            except Exception as e:
                # If drift detection fails, continue with drift_score = 0
                print(f"Warning: Drift detection failed: {e}")
                drift_score = 0.0
        
        # Get accuracy metrics
        recent_accuracy = feedback_metrics.get('accuracy', 85.0) / 100  # Convert to 0-1
        baseline_accuracy = 0.88  # From Phase 3 testing
        
        # Evaluate
        evaluation = self.trigger.evaluate(
            feedback_count=feedback_count,
            drift_score=drift_score,
            recent_accuracy=recent_accuracy,
            baseline_accuracy=baseline_accuracy
        )
        
        # Add recommendations
        evaluation['recommendations'] = self.trigger.get_recommendations(evaluation)
        evaluation['timestamp'] = datetime.now().isoformat()
        
        return evaluation

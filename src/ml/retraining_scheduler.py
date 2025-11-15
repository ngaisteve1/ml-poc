"""
Retraining Scheduler

Background job that periodically checks retraining conditions
and automatically triggers retraining when thresholds are met.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.feedback_db import FeedbackDB
from monitoring.predictions_db import PredictionsDB
from monitoring.drift_detector import DriftDetector
from monitoring.retraining_trigger import RetainingTriggerManager
from ml.retrain_model import ModelRetrainer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RetrainingScheduler:
    """Manages automatic retraining checks and execution"""
    
    def __init__(
        self,
        db_path: str = "monitoring.db",
        check_interval_hours: int = 4,
        auto_retrain: bool = True
    ):
        """
        Initialize scheduler
        
        Args:
            db_path: Path to monitoring database
            check_interval_hours: How often to check for retraining conditions
            auto_retrain: Whether to automatically trigger retraining when conditions met
        """
        self.db_path = db_path
        self.check_interval_hours = check_interval_hours
        self.auto_retrain = auto_retrain
        self.scheduler = None
        self.last_check = None
        self.last_retrain = None
    
    def _check_conditions(self):
        """Check if retraining conditions are met"""
        try:
            logger.info("🔍 Checking retraining conditions...")
            
            # Initialize databases
            feedback_db = FeedbackDB(self.db_path)
            predictions_db = PredictionsDB(self.db_path)
            drift_detector = DriftDetector()
            
            # Create trigger manager
            trigger_manager = RetainingTriggerManager(
                feedback_db=feedback_db,
                predictions_db=predictions_db,
                drift_detector=drift_detector
            )
            
            # Check conditions
            evaluation = trigger_manager.check_retraining_conditions()
            
            self.last_check = datetime.now()
            
            # Log results
            should_retrain = evaluation.get('should_retrain', False)
            confidence = evaluation.get('confidence', 0.0)
            
            if should_retrain:
                logger.warning(f"[WARNING] RETRAINING CONDITIONS MET!")
                logger.warning(f"   Reason: {evaluation['reason']}")
                logger.warning(f"   Confidence: {confidence:.2f}")
                
                if self.auto_retrain:
                    self._execute_retraining(evaluation)
                else:
                    logger.info("⏸️ Auto-retraining disabled - manual intervention required")
            else:
                logger.info(f"✅ Conditions not met: {evaluation['reason']}")
            
            # Log evaluation to file
            self._log_evaluation(evaluation)
            
            feedback_db.close()
            predictions_db.close()
            
        except Exception as e:
            logger.error(f"❌ Error checking conditions: {e}", exc_info=True)
    
    def _execute_retraining(self, evaluation: dict):
        """Execute the retraining process"""
        try:
            logger.info("[RETRAIN] Starting automatic retraining...")
            
            # Get metrics from evaluation
            metrics = evaluation.get('metrics', {})
            feedback_count = metrics.get('feedback_count', 0)
            drift_score = metrics.get('drift_score', 0.0)
            
            # Create retrainer
            retrainer = ModelRetrainer(db_path=self.db_path)
            
            # Execute retraining
            result = retrainer.retrain(
                feedback_count=feedback_count,
                drift_score=drift_score,
                contamination=0.1,
                days=90
            )
            
            if result['status'] == 'success':
                logger.info(f"[OK] Retraining completed successfully!")
                logger.info(f"   Run ID: {result['run_id']}")
                logger.info(f"   Model Path: {result['model_path']}")
                
                self.last_retrain = datetime.now()
                
                # Log success
                self._log_retrain_success(result, evaluation)
            else:
                logger.error(f"[ERROR] Retraining failed: {result.get('error', 'Unknown error')}")
                self._log_retrain_failure(result, evaluation)
        
        except Exception as e:
            logger.error(f"[ERROR] Error executing retraining: {e}", exc_info=True)
    
    def _log_evaluation(self, evaluation: dict):
        """Log evaluation results to file"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / "retraining_checks.jsonl"
            
            # Convert numpy types to native Python types for JSON serialization
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'should_retrain': bool(evaluation.get('should_retrain', False)),
                'confidence': float(evaluation.get('confidence', 0.0)),
                'conditions_met': int(evaluation.get('conditions_met', 0)),
                'metrics': {k: float(v) if isinstance(v, (int, float)) else v 
                           for k, v in evaluation.get('metrics', {}).items()}
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        
        except Exception as e:
            logger.warning(f"Could not log evaluation: {e}")
    
    def _log_retrain_success(self, result: dict, evaluation: dict):
        """Log successful retraining"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / "retraining_history.jsonl"
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'status': 'success',
                'run_id': result.get('run_id'),
                'model_path': result.get('model_path'),
                'trigger_metrics': evaluation.get('metrics', {}),
                'model_metrics': result.get('metrics', {})
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
        
        except Exception as e:
            logger.warning(f"Could not log retrain success: {e}")
    
    def _log_retrain_failure(self, result: dict, evaluation: dict):
        """Log failed retraining"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / "retraining_failures.jsonl"
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': result.get('error'),
                'trigger_metrics': evaluation.get('metrics', {})
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        
        except Exception as e:
            logger.warning(f"Could not log retrain failure: {e}")
    
    def start(self):
        """Start the background scheduler"""
        if self.scheduler is not None:
            logger.warning("Scheduler already running")
            return
        
        self.scheduler = BackgroundScheduler()
        
        # Add job to check conditions periodically
        self.scheduler.add_job(
            self._check_conditions,
            trigger=IntervalTrigger(hours=self.check_interval_hours),
            id='retrain_check',
            name='Check retraining conditions',
            replace_existing=True
        )
        
        self.scheduler.start()
        
        logger.info(f"[OK] Retraining scheduler started")
        logger.info(f"   Check interval: {self.check_interval_hours} hours")
        logger.info(f"   Auto-retrain: {'Enabled' if self.auto_retrain else 'Disabled'}")
        
        # Run first check immediately
        logger.info("Running initial check...")
        self._check_conditions()
    
    def stop(self):
        """Stop the background scheduler"""
        if self.scheduler is not None:
            self.scheduler.shutdown()
            logger.info("[OK] Retraining scheduler stopped")
            self.scheduler = None
    
    def trigger_check_now(self):
        """Manually trigger a check"""
        logger.info("Manually triggering retraining check...")
        self._check_conditions()
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        return {
            'running': self.scheduler is not None and self.scheduler.running,
            'check_interval_hours': self.check_interval_hours,
            'auto_retrain': self.auto_retrain,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_retrain': self.last_retrain.isoformat() if self.last_retrain else None
        }


# Global scheduler instance
_scheduler_instance: RetrainingScheduler = None


def get_scheduler(
    db_path: str = "monitoring.db",
    check_interval_hours: int = 4,
    auto_retrain: bool = True
) -> RetrainingScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = RetrainingScheduler(
            db_path=db_path,
            check_interval_hours=check_interval_hours,
            auto_retrain=auto_retrain
        )
    
    return _scheduler_instance


def start_scheduler(**kwargs) -> RetrainingScheduler:
    """Start the retraining scheduler"""
    scheduler = get_scheduler(**kwargs)
    scheduler.start()
    return scheduler


def stop_scheduler():
    """Stop the retraining scheduler"""
    global _scheduler_instance
    
    if _scheduler_instance is not None:
        _scheduler_instance.stop()
        _scheduler_instance = None


if __name__ == '__main__':
    # Example: Run scheduler in foreground
    logger.info("Starting Retraining Scheduler in foreground mode...")
    
    scheduler = RetrainingScheduler(
        db_path="monitoring.db",
        check_interval_hours=4,
        auto_retrain=True
    )
    
    try:
        scheduler.start()
        
        # Keep running
        import time
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()

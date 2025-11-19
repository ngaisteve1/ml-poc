"""
Test script to populate mock feedback data for demonstration
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

from src.monitoring.feedback_db import FeedbackDB
from src.monitoring.predictions_db import PredictionsDB
import random
from datetime import datetime, timedelta


def populate_mock_feedback():
    """Populate mock feedback data for testing"""
    
    feedback_db = FeedbackDB('monitoring.db')
    predictions_db = PredictionsDB('monitoring.db')
    
    print("📝 Populating mock feedback data...")
    
    # First, ensure we have some predictions
    print("\n1. Adding sample predictions...")
    for i in range(30):
        pred_date = (datetime.now() - timedelta(days=30-i)).strftime('%Y-%m-%d')
        predictions_db.save_prediction(
            prediction_date=pred_date,
            archived_gb_predicted=100 + random.uniform(-20, 20),
            savings_gb_predicted=45 + random.uniform(-5, 5)
        )
    print("✅ 30 predictions added")
    
    # Add feedback for some predictions
    print("\n2. Adding feedback records...")
    feedback_count = 0
    for i in range(60):  # Add 60 feedback records to exceed threshold of 50
        days_ago = random.randint(1, 30)
        pred_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        predicted_val = 100 + random.uniform(-20, 20)
        # 70% correct, 20% incorrect, 10% uncertain
        rand = random.random()
        if rand < 0.7:
            # Correct - actual is close to predicted
            actual_val = predicted_val + random.uniform(-5, 5)
            status = 'correct'
        elif rand < 0.9:
            # Incorrect - actual is far from predicted
            actual_val = predicted_val + random.uniform(-15, 15)
            status = 'incorrect'
        else:
            # Uncertain
            actual_val = predicted_val + random.uniform(-10, 10)
            status = 'uncertain'
        
        feedback_id = feedback_db.submit_feedback(
            prediction_id=None,
            prediction_date=pred_date,
            predicted_value=predicted_val,
            actual_value=actual_val,
            feedback_status=status,
            user_feedback="Test feedback" if random.random() < 0.3 else None
        )
        
        if feedback_id > 0:
            feedback_count += 1
    
    print(f"✅ {feedback_count} feedback records added")
    
    # Check feedback statistics
    print("\n3. Feedback Statistics:")
    recent_feedback = feedback_db.get_feedback_count(days=7)
    accuracy = feedback_db.get_feedback_accuracy(days=30)
    
    print(f"   Feedback in last 7 days: {recent_feedback}")
    print(f"   Total feedback: {accuracy['total_feedback']}")
    print(f"   Correct: {accuracy['correct_feedback']}")
    print(f"   Incorrect: {accuracy['incorrect_feedback']}")
    print(f"   Uncertain: {accuracy['uncertain_feedback']}")
    print(f"   Overall accuracy: {accuracy['accuracy']:.1f}%")
    print(f"   Avg error: {accuracy['avg_error']:.2f} GB")
    
    # Check retraining trigger conditions
    print("\n4. Retraining Trigger Conditions:")
    print(f"   Feedback count: {recent_feedback}/50 {'✅' if recent_feedback >= 50 else '❌'}")
    print(f"   Drift detection: Would need real drift detection to evaluate")
    print(f"   Accuracy drop: Would need baseline comparison")
    
    feedback_db.close()
    predictions_db.close()
    
    print("\n✅ Mock data population complete!")
    print("\n💡 Next step: Run 'streamlit run src/ui/streamlit_app.py' and check the Feedback & Retraining tabs")


if __name__ == "__main__":
    populate_mock_feedback()

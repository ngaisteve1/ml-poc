"""
SmartArchive Archive Forecast - Streamlit Dashboard

A web-based UI for viewing archive forecasts and predictions.
Currently uses mock data for demonstration.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="SmartArchive Forecast Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 0.5em;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1em;
        border-radius: 0.5em;
        margin: 0.5em 0;
    }
    .success {
        color: #09ab3b;
        font-weight: bold;
    }
    .warning {
        color: #ff9900;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Import mock data
from mock_data import get_mock_historical_data, get_mock_prediction, get_mock_metrics

# Import monitoring modules
try:
    from monitoring_dashboard import create_monitoring_dashboard
    MONITORING_AVAILABLE = True
except ImportError as e:
    MONITORING_AVAILABLE = False
    import warnings
    warnings.warn(f"Monitoring dashboard not available: {e}")

# Import feedback and retraining modules
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from monitoring.feedback_db import FeedbackDB
    from monitoring.retraining_trigger import RetainingTriggerManager
    from ml.retraining_scheduler import start_scheduler, stop_scheduler, get_scheduler
    FEEDBACK_AVAILABLE = True
except ImportError as e:
    FEEDBACK_AVAILABLE = False
    import warnings
    warnings.warn(f"Feedback modules not available: {e}")

# Import Azure ML endpoint client
try:
    import sys
    from pathlib import Path
    ml_path = str(Path(__file__).parent.parent / 'ml')
    if ml_path not in sys.path:
        sys.path.insert(0, ml_path)
    from azure_endpoint_client import AzureMLEndpointClient
    AZURE_ML_AVAILABLE = True
except ImportError as e:
    AZURE_ML_AVAILABLE = False
    import warnings
    warnings.warn(f"Azure ML endpoint client not available: {e}")


def load_sidebar():
    """Load sidebar filters"""
    st.sidebar.markdown("## ⚙️ Filters & Settings")
    
    # Date range selector
    st.sidebar.subheader("📅 Date Range")
    date_range = st.sidebar.radio(
        "Select Period:",
        options=["Last 3 Months", "Last 6 Months", "Last Year", "All Time"],
        index=1
    )
    
    # File type filter
    st.sidebar.subheader("📁 File Types")
    file_types = st.sidebar.multiselect(
        "Select file types to include:",
        options=["PDF", "DOCX", "XLSX", "Other"],
        default=["PDF", "DOCX", "XLSX", "Other"]
    )
    
    # Tenant selector (mock)
    st.sidebar.subheader("🏢 Tenant")
    tenant = st.sidebar.selectbox(
        "Select Tenant:",
        options=["All Tenants", "Tenant A", "Tenant B", "Tenant C"],
        index=0
    )
    
    # Site selector (mock)
    st.sidebar.subheader("📍 Site")
    site = st.sidebar.selectbox(
        "Select Site:",
        options=["All Sites", "Site 1", "Site 2", "Site 3"],
        index=0
    )
    
    # Model selector
    st.sidebar.subheader("🤖 Model")
    model_version = st.sidebar.selectbox(
        "Model Version:",
        options=["Production (v1.2)", "Staging (v1.1)", "Previous (v1.0)"],
        index=0
    )
    
    st.sidebar.divider()
    
    return {
        "date_range": date_range,
        "file_types": file_types,
        "tenant": tenant,
        "site": site,
        "model": model_version
    }


def create_header():
    """Create dashboard header"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="main-header">📊 Archive Forecast Dashboard</div>', unsafe_allow_html=True)
        st.markdown("*Predict archive volume and storage savings with AI-powered forecasting*")
    
    with col2:
        st.metric("Model Status", "🟢 Active", "v1.2")


def create_summary_metrics(metrics):
    """Display summary metrics"""
    st.subheader("📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Use new Azure ML metrics with fallback to legacy metrics
    current_size = metrics.get('current_size', metrics.get('avg_archived_gb', 0))
    current_size_delta = metrics.get('current_size_delta', 2.4)
    predicted_30d = metrics.get('predicted_30d', current_size + 20)
    predicted_30d_delta = metrics.get('predicted_30d_delta', 20)
    potential_savings = metrics.get('potential_savings', metrics.get('avg_savings_gb', 0))
    savings_percent = metrics.get('savings_percent', 46.7)
    model_accuracy = metrics.get('model_accuracy', metrics.get('r2_score', 0.875) * 100)
    
    with col1:
        st.metric(
            label="Current Archive Size",
            value=f"{current_size:.2f} GB",
            delta=f"+{current_size_delta:.2f} GB"
        )
    
    with col2:
        st.metric(
            label="Predicted (30 days)",
            value=f"{predicted_30d:.2f} GB",
            delta=f"+{predicted_30d_delta:.2f} GB"
        )
    
    with col3:
        st.metric(
            label="Potential Savings",
            value=f"{potential_savings:.2f} GB",
            delta=f"{savings_percent:.1f}%"
        )
    
    with col4:
        st.metric(
            label="Model Accuracy",
            value=f"{model_accuracy:.1f}%",
            delta="Stable"
        )


def create_historical_vs_predicted_chart(df_historical, df_predicted):
    """Create time series chart comparing historical and predicted data"""
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=df_historical['date'],
        y=df_historical['archived_gb'],
        mode='lines+markers',
        name='Historical Archive Size',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    # Predicted data
    fig.add_trace(go.Scatter(
        x=df_predicted['date'],
        y=df_predicted['archived_gb'],
        mode='lines+markers',
        name='Predicted Archive Size',
        line=dict(color='#ff7f0e', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    # Add confidence interval if available (for mock data compatibility)
    if 'confidence_upper' in df_predicted.columns and 'confidence_lower' in df_predicted.columns:
        fig.add_trace(go.Scatter(
            x=df_predicted['date'].tolist() + df_predicted['date'].tolist()[::-1],
            y=(df_predicted['archived_gb'] + df_predicted['confidence_upper']).tolist() + 
              (df_predicted['archived_gb'] - df_predicted['confidence_lower']).tolist()[::-1],
            fill='toself',
            fillcolor='rgba(255, 127, 14, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% Confidence Interval',
            hoverinfo='skip'
        ))
    
    fig.update_layout(
        title="Archive Volume: Historical vs Predicted",
        xaxis_title="Date",
        yaxis_title="Archive Size (GB)",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    return fig


def create_file_type_distribution(df):
    """Create pie chart of file type distribution"""
    file_types = ['PDF', 'DOCX', 'XLSX', 'Other']
    sizes = [35, 25, 20, 20]  # Mock percentages
    
    fig = px.pie(
        values=sizes,
        names=file_types,
        title='File Type Distribution in Archive',
        color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    )
    
    fig.update_layout(height=400)
    return fig


def create_savings_projection(df_predicted):
    """Create savings projection chart"""
    df_predicted_copy = df_predicted.copy()
    df_predicted_copy['cumulative_savings'] = df_predicted_copy['savings_gb'].cumsum()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_predicted_copy['date'],
        y=df_predicted_copy['savings_gb'],
        name='Monthly Savings',
        marker_color='#2ca02c',
        opacity=0.7
    ))
    
    fig.add_trace(go.Scatter(
        x=df_predicted_copy['date'],
        y=df_predicted_copy['cumulative_savings'],
        name='Cumulative Savings',
        line=dict(color='#d62728', width=3),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Storage Savings Projection',
        xaxis_title='Date',
        yaxis_title='Monthly Savings (GB)',
        yaxis2=dict(
            title='Cumulative Savings (GB)',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    return fig


def create_scenario_simulator():
    """Create scenario simulation section"""
    st.subheader("🔮 Scenario Simulator")
    st.markdown("*Simulate different archive strategies and see the impact*")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        archive_frequency = st.slider(
            "Archive Frequency (files/day)",
            min_value=100,
            max_value=1000,
            value=320,
            step=50
        )
    
    with col2:
        avg_file_size = st.slider(
            "Average File Size (MB)",
            min_value=0.5,
            max_value=5.0,
            value=1.2,
            step=0.1
        )
    
    with col3:
        retention_period = st.slider(
            "Retention Period (days)",
            min_value=30,
            max_value=365,
            value=90,
            step=30
        )
    
    # Calculate impact
    simulated_growth = (archive_frequency * avg_file_size * retention_period) / 1024
    
    st.markdown("### 📊 Simulated Impact")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Projected Archive Size",
            f"{simulated_growth:.2f} GB",
            "Simulated"
        )
    
    with col2:
        st.metric(
            "Monthly Growth",
            f"{(archive_frequency * avg_file_size * 30) / 1024:.2f} GB",
            "Estimated"
        )
    
    with col3:
        st.metric(
            "Yearly Projection",
            f"{(simulated_growth * 4):.2f} GB",
            "Forecast"
        )


def create_model_performance_section(metrics):
    """Display model performance metrics"""
    st.subheader("🎯 Model Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Accuracy Metrics**")
        # Use safe metric retrieval with fallbacks
        r2_score = metrics.get('r2_score', 0.875)
        rmse = metrics.get('rmse', 12.34)
        mae = metrics.get('mae', 8.92)
        mape = metrics.get('mape', 5.2)
        
        performance_df = pd.DataFrame({
            'Metric': ['R² Score', 'RMSE (GB)', 'MAE (GB)', 'MAPE (%)'],
            'Value': [r2_score, rmse, mae, mape]
        })
        st.dataframe(performance_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**Model Info**")
        info_df = pd.DataFrame({
            'Property': ['Model Type', 'Features', 'Training Data', 'Last Updated'],
            'Details': [
                'Random Forest + MultiOutput',
                '9 features',
                '12 months historical',
                datetime.now().strftime('%Y-%m-%d %H:%M')
            ]
        })
        st.dataframe(info_df, use_container_width=True, hide_index=True)


def create_feedback_section():
    """Create feedback collection interface"""
    st.subheader("📝 Model Feedback")
    st.markdown("*Help us improve the model by providing feedback on predictions*")
    
    if not FEEDBACK_AVAILABLE:
        st.warning("⚠️ Feedback module not available")
        return
    
    try:
        # Initialize feedback database
        feedback_db = FeedbackDB('monitoring.db')
        
        # Create two columns
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Show recent predictions
            st.markdown("**Recent Predictions**")
            recent_preds = feedback_db.get_recent_feedback(days=30, limit=10)
            
            if not recent_preds.empty:
                # Display table
                display_cols = ['prediction_date', 'predicted_value', 'actual_value', 'feedback_status']
                display_df = recent_preds[display_cols].copy()
                display_df['prediction_date'] = pd.to_datetime(display_df['prediction_date']).dt.strftime('%Y-%m-%d')
                display_df = display_df.rename(columns={
                    'prediction_date': 'Date',
                    'predicted_value': 'Predicted',
                    'actual_value': 'Actual',
                    'feedback_status': 'Status'
                })
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No feedback records yet. Submit your first feedback below!")
        
        with col2:
            # Feedback stats
            st.markdown("**Feedback Stats**")
            accuracy = feedback_db.get_feedback_accuracy(days=30)
            
            st.metric("Total Feedback", accuracy['total_feedback'])
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Correct", accuracy['correct_feedback'])
            with col_b:
                st.metric("Incorrect", accuracy['incorrect_feedback'])
        
        st.divider()
        
        # Feedback submission form
        st.markdown("**Submit New Feedback**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            pred_date = st.date_input(
                "Prediction Date",
                value=datetime.now().date(),
                key="feedback_pred_date"
            )
        
        with col2:
            predicted_val = st.number_input(
                "Predicted Value (GB)",
                value=0.0,
                step=0.1,
                key="feedback_pred_val"
            )
        
        with col3:
            actual_val = st.number_input(
                "Actual Value (GB)",
                value=0.0,
                step=0.1,
                key="feedback_actual_val"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            feedback_status = st.radio(
                "Was this prediction correct?",
                ["✅ Correct", "❌ Incorrect", "🤷 Uncertain"],
                key="feedback_status"
            )
            # Extract status value
            status_map = {"✅ Correct": "correct", "❌ Incorrect": "incorrect", "🤷 Uncertain": "uncertain"}
            status = status_map[feedback_status]
        
        with col2:
            user_comment = st.text_input(
                "Additional Comments (optional)",
                key="feedback_comment"
            )
        
        if st.button("📤 Submit Feedback", key="submit_feedback_btn", use_container_width=True):
            try:
                feedback_db.submit_feedback(
                    prediction_id=None,  # Will be linked to actual prediction if available
                    prediction_date=pred_date.strftime('%Y-%m-%d'),
                    predicted_value=predicted_val,
                    actual_value=actual_val,
                    feedback_status=status,
                    user_feedback=user_comment
                )
                st.success("✅ Feedback submitted successfully! Thank you for helping us improve.")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error submitting feedback: {e}")
        
        feedback_db.close()
    
    except Exception as e:
        st.error(f"⚠️ Error in feedback section: {e}")


def create_retraining_status_section():
    """Display retraining status and conditions"""
    st.subheader("🔄 Retraining Status")
    
    if not FEEDBACK_AVAILABLE:
        st.warning("⚠️ Retraining module not available - feedback system not loaded")
        return
    
    try:
        # Initialize databases
        try:
            feedback_db = FeedbackDB('monitoring.db')
        except Exception as e:
            st.warning(f"⚠️ Could not initialize feedback database: {str(e)}")
            st.info("💡 **First-time setup**: The feedback database will be created when you submit your first feedback entry in Tab 4.")
            return
        
        try:
            # Import locally to avoid startup issues
            from monitoring.predictions_db import PredictionsDB
            from monitoring.drift_detector import DriftDetector
            
            predictions_db = PredictionsDB('monitoring.db')
            drift_detector = DriftDetector()
        except Exception as e:
            st.warning(f"⚠️ Could not initialize analysis components: {str(e)}")
            feedback_db.close()
            return
        
        # Create trigger manager
        trigger_manager = RetainingTriggerManager(
            feedback_db=feedback_db,
            predictions_db=predictions_db,
            drift_detector=drift_detector
        )
        
        # Check conditions
        try:
            evaluation = trigger_manager.check_retraining_conditions()
        except Exception as e:
            st.warning(f"⚠️ Error checking retraining conditions: {str(e)}")
            st.info("💡 **This is expected during initial setup**. Submit feedback in Tab 4 to populate the system and enable retraining status.")
            feedback_db.close()
            predictions_db.close()
            return
        
        # Display status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "🟢 READY" if evaluation['should_retrain'] else "🔵 MONITORING"
            st.metric("Retraining Status", status)
        
        with col2:
            metrics = evaluation['metrics']
            st.metric(
                "Feedback Count",
                f"{metrics['feedback_count']}/50",
                f"{metrics['feedback_count']}%"
            )
        
        with col3:
            st.metric(
                "Drift Score",
                f"{metrics['drift_score']:.2f}",
                f"Threshold: 0.30"
            )
        
        # Display detailed conditions
        st.markdown("**Evaluation Details**")
        
        col1, col2, col3 = st.columns(3)
        
        details = evaluation['trigger_details']
        
        with col1:
            status_icon = "✅" if details['condition_feedback'] else "❌"
            st.markdown(f"{status_icon} **Feedback** ({metrics['feedback_count']}/{details['feedback_threshold']})")
        
        with col2:
            status_icon = "✅" if details['condition_drift'] else "❌"
            st.markdown(f"{status_icon} **Drift** ({metrics['drift_score']:.2f}/{details['drift_threshold']})")
        
        with col3:
            accuracy_drop = metrics['accuracy_drop'] * 100
            status_icon = "✅" if details['condition_accuracy'] else "❌"
            st.markdown(f"{status_icon} **Accuracy** ({accuracy_drop:.1f}%/{details['accuracy_drop_threshold']*100:.1f}%)")
        
        st.divider()
        
        # Show recommendations
        if 'recommendations' in evaluation:
            recs = evaluation['recommendations']
            st.markdown("**Recommendations**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Action**: {recs['action'].upper()}\n**Urgency**: {recs['urgency'].upper()}")
            
            with col2:
                data_needed = recs['data_needed']
                st.info(f"**More Feedback Needed**: {data_needed['more_feedback_needed']}\n**Est. Days**: {data_needed['days_to_threshold']}")
        
        # Display retraining history
        st.markdown("**Recent Retraining History**")
        history = feedback_db.get_retraining_history(limit=5)
        
        if not history.empty:
            display_cols = ['started_at', 'trigger_reason', 'feedback_count', 'status']
            display_df = history[display_cols].copy()
            display_df['started_at'] = pd.to_datetime(display_df['started_at']).dt.strftime('%Y-%m-%d %H:%M')
            display_df = display_df.rename(columns={'started_at': 'Date', 'trigger_reason': 'Reason'})
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No retraining events yet.")
        
        feedback_db.close()
        predictions_db.close()
    
    except Exception as e:
        st.warning("⚠️ Retraining Status")
        st.info("""
### 💡 How to Use Retraining:

**Locally** (Recommended for testing):
1. Go to Tab 4 (Feedback) and submit predictions
2. Retraining status will show in this tab
3. Scheduler will auto-trigger when conditions are met

**On Streamlit Cloud**:
- Data doesn't persist between app restarts (Streamlit limitation)
- For production: See `docs/STREAMLIT_CLOUD_RETRAINING.md` for setup

**Current Status**: System initialized but no data yet.

👉 **Try**: Go to Tab 4 → Submit feedback → Return here to see status
        """)


def create_data_table(df_predicted):
    """Display detailed prediction data"""
    st.subheader("📋 Detailed Predictions")
    
    # Format dataframe for display
    display_df = df_predicted.copy()
    display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
    display_df = display_df.round(2)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Download button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f"archive_forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def main():
    """Main dashboard function"""
    
    # Load filters
    filters = load_sidebar()
    
    # Create header
    create_header()
    
    st.divider()
    
    # Create main tabs for different views
    tab_forecast, tab_analysis, tab_monitoring, tab_feedback, tab_retraining = st.tabs([
        "📊 Forecast & Predictions",
        "📈 Analysis",
        "🔍 Monitoring",
        "📝 Feedback",
        "🔄 Retraining"
    ])
    
    # Load data and get predictions
    df_historical = get_mock_historical_data()
    
    # Try to get real predictions from Azure ML, fall back to mock if unavailable
    try:
        if AZURE_ML_AVAILABLE:
            st.info("🔄 Fetching predictions from Azure ML endpoint...")
            client = AzureMLEndpointClient()
            df_predicted, metrics = client.get_predictions(df_historical, forecast_days=90)
            st.success("✅ Real predictions loaded from Azure ML!")
        else:
            st.warning("⚠️ Azure ML endpoint not available, using mock predictions")
            df_predicted = get_mock_prediction()
            metrics = get_mock_metrics()
    except Exception as e:
        st.warning(f"⚠️ Could not load Azure ML predictions: {str(e)}. Using mock predictions instead.")
        df_predicted = get_mock_prediction()
        metrics = get_mock_metrics()
    
    # TAB 1: Forecast & Predictions
    with tab_forecast:
        # Summary metrics
        create_summary_metrics(metrics)
        
        st.divider()
        
        # Time series chart
        st.subheader("📈 Historical vs Predicted")
        fig_timeseries = create_historical_vs_predicted_chart(df_historical, df_predicted)
        st.plotly_chart(fig_timeseries, use_container_width=True)
        
        # Savings projection
        st.subheader("💰 Savings Projection")
        fig_savings = create_savings_projection(df_predicted)
        st.plotly_chart(fig_savings, use_container_width=True)
        
        # Data table and export
        st.divider()
        create_data_table(df_predicted)
    
    # TAB 2: Analysis & Trends
    with tab_analysis:
        # Charts section
        st.subheader("📉 Analysis & Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_filetypes = create_file_type_distribution(df_historical)
            st.plotly_chart(fig_filetypes, use_container_width=True)
        
        with col2:
            st.info("📊 File type distribution and trends")
            st.write("Analyze distribution of file types in archive")
        
        st.divider()
        
        # Scenario simulator
        create_scenario_simulator()
        
        st.divider()
        
        # Model performance
        create_model_performance_section(metrics)
    
    # TAB 3: Monitoring Dashboard
    with tab_monitoring:
        if MONITORING_AVAILABLE:
            create_monitoring_dashboard()
        else:
            st.warning("⚠️ Monitoring dashboard is not available. Install required dependencies.")
            st.info("To enable monitoring, ensure the monitoring module is properly configured.")
    
    # TAB 4: Feedback Collection
    with tab_feedback:
        create_feedback_section()
    
    # TAB 5: Retraining Status
    with tab_retraining:
        create_retraining_status_section()
    
    # Footer
    st.divider()
    st.markdown("""
    ---
    **SmartArchive Archive Forecast System**
    
    📊 Dashboard Version 2.0 | 🤖 Model v1.2 | 🔍 Monitoring v1.0
    
    *For questions or feedback, contact the SmartArchive team.*
    """)


if __name__ == "__main__":
    main()

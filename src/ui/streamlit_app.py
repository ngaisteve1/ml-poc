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
from mock_data import (
    get_mock_historical_data, 
    get_mock_prediction, 
    get_mock_metrics,
    get_query1_monthly_trends,
    get_query2_file_type_distribution,
    get_query3_storage_saved,
    get_query4_job_execution,
    get_query5_tenant_performance,
    get_query6_weekly_trends,
    get_query7_archive_state,
    get_query8_size_distribution,
    get_query9_consolidated_dataset,
)

# Import monitoring modules
try:
    from monitoring_dashboard import create_monitoring_dashboard
    MONITORING_AVAILABLE = True
except ImportError as e:
    MONITORING_AVAILABLE = False
    import warnings
    warnings.warn(f"Monitoring dashboard not available: {e}")

# Import cost monitoring module
try:
    from cost_monitoring import create_cost_monitoring_dashboard
    COST_MONITORING_AVAILABLE = True
except ImportError as e:
    COST_MONITORING_AVAILABLE = False
    import warnings
    warnings.warn(f"Cost monitoring module not available: {e}")

# Import feedback and retraining modules
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Try to use cloud-compatible version first, fall back to original
    try:
        from monitoring.feedback_db_cloud import FeedbackDB
        print("✅ Using cloud-compatible feedback database")
    except ImportError:
        from monitoring.feedback_db import FeedbackDB
        print("✅ Using standard feedback database")
    
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
        # Initialize feedback database with caching for Streamlit Cloud
        @st.cache_resource
        def get_feedback_db():
            """Cache feedback database connection across reruns"""
            import os
            
            use_cloud = os.getenv('USE_CLOUD_DB', 'false').lower() == 'true'
            
            if use_cloud:
                # Use cloud database for production
                cloud_config = {
                    'provider': os.getenv('DB_PROVIDER', 'azure'),
                    'host': os.getenv('AZURE_SQL_HOST') or os.getenv('POSTGRES_HOST'),
                    'user': os.getenv('AZURE_SQL_USER') or os.getenv('POSTGRES_USER'),
                    'password': os.getenv('AZURE_SQL_PASSWORD') or os.getenv('POSTGRES_PASSWORD'),
                    'database': os.getenv('AZURE_SQL_DATABASE') or os.getenv('POSTGRES_DATABASE')
                }
                print("🌐 Connecting to cloud database...")
                return FeedbackDB(use_cloud=True, cloud_config=cloud_config)
            else:
                # Use SQLite locally (development)
                print("💾 Using local SQLite database...")
                return FeedbackDB('monitoring.db')
        
        feedback_db = get_feedback_db()
        
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
                # Clear the form by rerunning
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error submitting feedback: {e}")
    
    except Exception as e:
        st.error(f"⚠️ Error in feedback section: {e}")


def create_retraining_status_section():
    """Display retraining status and conditions"""
    st.subheader("🔄 Retraining Status")
    
    if not FEEDBACK_AVAILABLE:
        st.warning("⚠️ Retraining module not available - feedback system not loaded")
        return
    
    try:
        # Initialize databases with caching
        @st.cache_resource
        def get_databases():
            """Cache database connections across reruns"""
            import os
            
            use_cloud = os.getenv('USE_CLOUD_DB', 'false').lower() == 'true'
            
            if use_cloud:
                cloud_config = {
                    'provider': os.getenv('DB_PROVIDER', 'azure'),
                    'host': os.getenv('AZURE_SQL_HOST') or os.getenv('POSTGRES_HOST'),
                    'user': os.getenv('AZURE_SQL_USER') or os.getenv('POSTGRES_USER'),
                    'password': os.getenv('AZURE_SQL_PASSWORD') or os.getenv('POSTGRES_PASSWORD'),
                    'database': os.getenv('AZURE_SQL_DATABASE') or os.getenv('POSTGRES_DATABASE')
                }
                feedback_db = FeedbackDB(use_cloud=True, cloud_config=cloud_config)
            else:
                feedback_db = FeedbackDB('monitoring.db')
            
            return feedback_db
        
        feedback_db = get_databases()
        
        try:
            # Import locally to avoid startup issues
            from monitoring.predictions_db import PredictionsDB
            from monitoring.drift_detector import DriftDetector
            
            predictions_db = PredictionsDB('monitoring.db')
            drift_detector = DriftDetector()
        except Exception as e:
            st.warning(f"⚠️ Could not initialize analysis components: {str(e)}")
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
    
    except Exception as e:
        st.warning("⚠️ Retraining Status")
        st.info("""
### 💡 How to Use Retraining:

**Locally** (Recommended for testing):
1. Go to Tab 4 (Feedback) and submit predictions
2. Retraining status will show in this tab
3. Scheduler will auto-trigger when conditions are met

**On Streamlit Cloud** (Production):
- SQLite doesn't persist between restarts
- Use cloud database: See `.env.streamlit.example` for setup
- Follow Option 1 Implementation Guide: `docs/OPTION1-IMPLEMENTATION-GUIDE.md`

**Current Status**: System initialized but no data yet.

👉 **Quick Start**: 
1. Go to Tab 4 → Submit feedback
2. Return here to see status
3. For cloud: Configure `.env` with Azure SQL or PostgreSQL

**For Streamlit Cloud production:**
- Copy `.env.streamlit.example` to `.streamlit/secrets.toml`
- Fill in cloud database credentials
- App will automatically use cloud database
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


def create_exploration_dashboard():
    """
    Create comprehensive data exploration dashboard for Queries 1-9.
    
    This section provides visualizations for understanding archive patterns,
    file distributions, and features used in ML model training.
    
    Includes:
    - Query 1: Monthly trends
    - Query 2: File type distribution
    - Query 3: Storage savings
    - Query 4: Job execution patterns
    - Query 5: Tenant performance
    - Query 6: Weekly trends
    - Query 7: Archive state distribution
    - Query 8: File size quantiles
    - Query 9: Consolidated dataset overview
    """
    st.subheader("🔍 Data Exploration & Feature Engineering")
    st.markdown("*Analyze archive patterns across all dimensions for model training insights*")
    
    # Create sub-tabs for different exploration areas
    exp_tab1, exp_tab2, exp_tab3, exp_tab4 = st.tabs([
        "📊 Query 1-3: Volume & Savings",
        "🏢 Query 4-5: Jobs & Tenants",
        "📈 Query 6-8: Trends & Distribution",
        "🎓 Query 9: Training Dataset"
    ])
    
    # ============================================================
    # Tab 1: Query 1, 2, 3 - Volume, File Types, Savings
    # ============================================================
    with exp_tab1:
        st.markdown("### Query 1: Monthly Archive Volume Trends")
        st.markdown("*Aggregates archived files by month to show volume trends*")
        
        df_q1 = get_query1_monthly_trends()
        
        # Volume trend chart
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_q1 = go.Figure()
            fig_q1.add_trace(go.Scatter(
                x=df_q1['period'],
                y=df_q1['volume_gb'],
                mode='lines+markers',
                name='Archive Volume (GB)',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=8, color='#1f77b4'),
                hovertemplate='<b>%{x|%Y-%m}</b><br>Volume: %{y:.2f} GB<extra></extra>'
            ))
            fig_q1.update_layout(
                title='Monthly Archive Volume Growth',
                xaxis_title='Month',
                yaxis_title='Volume (GB)',
                height=350,
                template='plotly_white',
                hovermode='x unified'
            )
            st.plotly_chart(fig_q1, use_container_width=True)
        
        with col2:
            st.metric("Latest Volume", f"{df_q1['volume_gb'].iloc[-1]:.1f} GB")
            st.metric("Growth Rate", f"{((df_q1['volume_gb'].iloc[-1] / df_q1['volume_gb'].iloc[0]) - 1) * 100:.1f}%")
            st.metric("Avg Monthly", f"{df_q1['volume_gb'].mean():.1f} GB")
        
        # Monthly details table
        st.markdown("**Monthly Statistics**")
        display_q1 = df_q1.copy()
        display_q1['period'] = display_q1['period'].dt.strftime('%Y-%m')
        display_q1 = display_q1[['period', 'files_archived', 'volume_gb', 'avg_file_size_mb']].round(2)
        display_q1.columns = ['Month', 'Files Archived', 'Volume (GB)', 'Avg Size (MB)']
        st.dataframe(display_q1, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Query 2: File Type Distribution
        st.markdown("### Query 2: File Type Distribution & Patterns")
        st.markdown("*Shows which file types are most prevalent in archive*")
        
        df_q2 = get_query2_file_type_distribution()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Pie chart
            fig_q2_pie = px.pie(
                df_q2,
                values='Percentage',
                names='FileType',
                title='File Type Distribution (%)',
                color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
            )
            fig_q2_pie.update_layout(height=350)
            st.plotly_chart(fig_q2_pie, use_container_width=True)
        
        with col2:
            # Bar chart by file count
            fig_q2_bar = go.Figure(data=[
                go.Bar(
                    x=df_q2['FileType'],
                    y=df_q2['FilesCount'],
                    marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
                    hovertemplate='<b>%{x}</b><br>Files: %{y:,.0f}<extra></extra>'
                )
            ])
            fig_q2_bar.update_layout(
                title='File Count by Type',
                xaxis_title='File Type',
                yaxis_title='Count',
                height=350,
                template='plotly_white'
            )
            st.plotly_chart(fig_q2_bar, use_container_width=True)
        
        # File type details table
        st.markdown("**File Type Details**")
        display_q2 = df_q2[['FileType', 'Percentage', 'FilesCount', 'TotalSizeGB']].copy()
        display_q2['Percentage'] = display_q2['Percentage'].round(2)
        display_q2.columns = ['Type', 'Percent (%)', 'File Count', 'Size (GB)']
        st.dataframe(display_q2, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Query 3: Storage Saved
        st.markdown("### Query 3: Storage Space Saved")
        st.markdown("*Files deleted after archiving = actual storage cost reduction*")
        
        df_q3 = get_query3_storage_saved()
        df_q3['month'] = pd.to_datetime(df_q3['month'])
        
        fig_q3 = go.Figure()
        fig_q3.add_trace(go.Bar(
            x=df_q3['month'],
            y=df_q3['storage_saved_gb'],
            marker_color='#2ca02c',
            name='Storage Saved',
            hovertemplate='<b>%{x|%Y-%m}</b><br>Saved: %{y:.2f} GB<extra></extra>'
        ))
        
        fig_q3.add_trace(go.Scatter(
            x=df_q3['month'],
            y=df_q3['storage_saved_gb'].cumsum(),
            mode='lines+markers',
            name='Cumulative Saved',
            line=dict(color='#d62728', width=2),
            yaxis='y2',
            hovertemplate='<b>%{x|%Y-%m}</b><br>Cumulative: %{y:.2f} GB<extra></extra>'
        ))
        
        fig_q3.update_layout(
            title='Monthly Storage Savings',
            xaxis_title='Month',
            yaxis_title='Monthly Savings (GB)',
            yaxis2=dict(title='Cumulative Savings (GB)', overlaying='y', side='right'),
            height=350,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_q3, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Saved", f"{df_q3['storage_saved_gb'].sum():.1f} GB")
        with col2:
            st.metric("Monthly Avg", f"{df_q3['storage_saved_gb'].mean():.1f} GB")
        with col3:
            st.metric("Latest Month", f"{df_q3['storage_saved_gb'].iloc[-1]:.1f} GB")
    
    # ============================================================
    # Tab 2: Query 4, 5 - Job Execution, Tenant Performance
    # ============================================================
    with exp_tab2:
        st.markdown("### Query 4: Archive Job Execution History")
        st.markdown("*Shows job patterns and recurrence frequency*")
        
        df_q4 = get_query4_job_execution()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Job type distribution
            fig_q4_type = px.bar(
                df_q4,
                x='JobType',
                y='TotalFilesArchived',
                color='JobType',
                title='Files Archived by Job Type',
                color_discrete_map={'Incremental': '#1f77b4', 'Full': '#ff7f0e'},
                labels={'TotalFilesArchived': 'Files Count'}
            )
            fig_q4_type.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_q4_type, use_container_width=True)
        
        with col2:
            # Job frequency
            fig_q4_freq = px.bar(
                df_q4,
                x='JobId',
                y='AvgDaysBetweenArchives',
                title='Archive Frequency by Job',
                color='AvgDaysBetweenArchives',
                color_continuous_scale='Viridis',
                labels={'AvgDaysBetweenArchives': 'Days Between Archives', 'JobId': 'Job ID'}
            )
            fig_q4_freq.update_layout(height=350)
            st.plotly_chart(fig_q4_freq, use_container_width=True)
        
        # Job details table
        st.markdown("**Job Execution Details**")
        display_q4 = df_q4.copy()
        display_q4.columns = ['Job ID', 'Tenant ID', 'Type', 'Files Archived', 'Days Between Archives']
        st.dataframe(display_q4, use_container_width=True, hide_index=True)
        
        st.divider()
        
        st.markdown("### Query 5: Tenant-Level Archive Performance")
        st.markdown("*Aggregated metrics per tenant for multi-tenant analysis*")
        
        df_q5 = get_query5_tenant_performance()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Tenant archive volume
            fig_q5 = px.scatter(
                df_q5,
                x='TotalFilesArchived',
                y='TotalArchiveVolumeGB',
                size='UniqueSitesArchived',
                color='StorageSavedGB',
                hover_name='TenantId',
                title='Tenant Archive Volume vs Files Archived',
                color_continuous_scale='Viridis',
                labels={
                    'TotalFilesArchived': 'Total Files Archived',
                    'TotalArchiveVolumeGB': 'Archive Volume (GB)',
                    'StorageSavedGB': 'Storage Saved (GB)'
                }
            )
            fig_q5.update_layout(height=350)
            st.plotly_chart(fig_q5, use_container_width=True)
        
        with col1:
            # Savings percentage
            fig_q5_save = px.box(
                df_q5,
                y='DeletedPercentage',
                title='Storage Savings Rate Distribution (%)',
                points='all'
            )
            fig_q5_save.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_q5_save, use_container_width=True)
        
        with col2:
            st.metric("Total Tenants", len(df_q5))
            st.metric("Avg Volume/Tenant", f"{df_q5['TotalArchiveVolumeGB'].mean():.1f} GB")
            st.metric("Avg Savings Rate", f"{df_q5['DeletedPercentage'].mean():.1f}%")
        
        # Tenant details table
        st.markdown("**Top 10 Tenants by Volume**")
        top_tenants = df_q5.nlargest(10, 'TotalArchiveVolumeGB')[
            ['TenantId', 'TotalFilesArchived', 'UniqueSitesArchived', 'TotalArchiveVolumeGB', 'StorageSavedGB']
        ].copy()
        top_tenants.columns = ['Tenant ID', 'Files', 'Sites', 'Volume (GB)', 'Saved (GB)']
        st.dataframe(top_tenants, use_container_width=True, hide_index=True)
    
    # ============================================================
    # Tab 3: Query 6, 7, 8 - Trends, States, Distribution
    # ============================================================
    with exp_tab3:
        st.markdown("### Query 6: Weekly Archive Trend Data")
        st.markdown("*Fine-grained time-series data for pattern detection*")
        
        df_q6 = get_query6_weekly_trends()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_q6 = go.Figure()
            fig_q6.add_trace(go.Scatter(
                x=df_q6['Date'],
                y=df_q6['FilesArchivedCount'],
                mode='lines',
                name='Weekly Files',
                line=dict(color='#1f77b4'),
                hovertemplate='<b>Week %{x|%U}</b><br>Files: %{y:,.0f}<extra></extra>'
            ))
            fig_q6.update_layout(
                title='Weekly Archive Trend',
                xaxis_title='Date',
                yaxis_title='Files Archived',
                height=350,
                template='plotly_white'
            )
            st.plotly_chart(fig_q6, use_container_width=True)
        
        with col2:
            st.metric("Avg Weekly Files", f"{df_q6['FilesArchivedCount'].mean():,.0f}")
            st.metric("Weekly Volatility", f"{df_q6['FilesArchivedCount'].std():,.0f}")
        
        st.divider()
        
        st.markdown("### Query 7: Archive State Distribution")
        st.markdown("*Shows data quality and processing status*")
        
        df_q7 = get_query7_archive_state()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig_q7_pie = px.pie(
                df_q7,
                values='FileCount',
                names='FileState',
                title='Archive State Distribution',
                color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            )
            fig_q7_pie.update_layout(height=350)
            st.plotly_chart(fig_q7_pie, use_container_width=True)
        
        with col2:
            fig_q7_bar = go.Figure(data=[
                go.Bar(
                    x=df_q7['FileState'],
                    y=df_q7['TotalSizeGB'],
                    marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
                    hovertemplate='<b>%{x}</b><br>Size: %{y:.1f} GB<extra></extra>'
                )
            ])
            fig_q7_bar.update_layout(
                title='Archive State by Size',
                xaxis_title='State',
                yaxis_title='Size (GB)',
                height=350,
                template='plotly_white'
            )
            st.plotly_chart(fig_q7_bar, use_container_width=True)
        
        # State details
        st.markdown("**Archive State Details**")
        display_q7 = df_q7[['FileState', 'FileCount', 'TotalSizeGB', 'PercentOfTotal']].copy()
        display_q7['PercentOfTotal'] = (display_q7['PercentOfTotal'] * 100).round(2)
        display_q7.columns = ['State', 'Count', 'Size (GB)', 'Percent (%)']
        st.dataframe(display_q7, use_container_width=True, hide_index=True)
        
        st.divider()
        
        st.markdown("### Query 8: File Size Distribution (Quantiles)")
        st.markdown("*Understanding file size patterns helps with capacity planning*")
        
        df_q8 = get_query8_size_distribution()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig_q8 = go.Figure(data=[
                go.Bar(
                    x=df_q8['Percentile'],
                    y=df_q8['FileSizeMB'],
                    marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
                    hovertemplate='<b>%{x}</b><br>Size: %{y:.1f} MB<extra></extra>'
                )
            ])
            fig_q8.update_layout(
                title='File Size Distribution (Quantiles)',
                xaxis_title='Percentile',
                yaxis_title='File Size (MB)',
                height=350,
                template='plotly_white'
            )
            st.plotly_chart(fig_q8, use_container_width=True)
        
        with col2:
            st.markdown("**Percentile Explanation**")
            st.info("""
            - **Q1 (25%)**: 25% of files are smaller than this
            - **Q2 (Median)**: 50% of files are smaller than this
            - **Q3 (75%)**: 75% of files are smaller than this
            - **P95**: 95% of files are smaller (outliers start)
            - **P99**: 99% of files are smaller (extreme outliers)
            """)
        
        # Size distribution table
        st.markdown("**File Size Quantiles**")
        display_q8 = df_q8[['Percentile', 'FileSizeMB', 'Description']].copy()
        display_q8.columns = ['Percentile', 'Size (MB)', 'Description']
        st.dataframe(display_q8, use_container_width=True, hide_index=True)
    
    # ============================================================
    # Tab 4: Query 9 - Consolidated Training Dataset
    # ============================================================
    with exp_tab4:
        st.markdown("### Query 9: Consolidated Training Dataset")
        st.markdown("*All 13 features from training_data.csv for ML model training*")
        
        df_q9 = get_query9_consolidated_dataset()
        
        # Feature info
        st.info("""
        **13 Features in Training Dataset:**
        
        **Time & Period** (1):
        - `period` - Date (YYYY-MM-01 format)
        
        **Volume Metrics** (3):
        - `files_archived` - Number of files archived monthly
        - `volume_gb` - Total archive volume in GB
        - `storage_saved_gb` - Storage freed from deletions
        
        **File Size Metrics** (2):
        - `avg_file_size_mb` - Average file size
        - `largest_file_mb` - Largest file size in dataset
        
        **File Type Distribution** (3):
        - `pct_pdf` - Percentage of PDF files
        - `pct_docx` - Percentage of Word documents
        - `pct_xlsx` - Percentage of Excel files
        
        **Engagement & Frequency** (2):
        - `archive_frequency_per_day` - Files archived per day
        - `deleted_files_count` - Number of files deleted after archiving
        
        **Tenant/Site Metrics** (2):
        - `tenant_count` - Number of active tenants
        - `site_count` - Number of active sites
        """)
        
        # Feature correlation visualization
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Volume trends across months
            fig_q9_trend = go.Figure()
            fig_q9_trend.add_trace(go.Scatter(
                x=df_q9['MonthStart'],
                y=df_q9['VolumeGBArchived'],
                mode='lines+markers',
                name='Archive Volume',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=8),
                hovertemplate='<b>%{x|%Y-%m}</b><br>Volume: %{y:.2f} GB<extra></extra>'
            ))
            fig_q9_trend.update_layout(
                title='Training Data: Archive Volume Over Time',
                xaxis_title='Month',
                yaxis_title='Volume (GB)',
                height=350,
                template='plotly_white'
            )
            st.plotly_chart(fig_q9_trend, use_container_width=True)
        
        with col2:
            # File type composition stacked area
            fig_q9_stack = go.Figure()
            fig_q9_stack.add_trace(go.Scatter(
                x=df_q9['MonthStart'],
                y=df_q9['PDFPercent'],
                mode='lines',
                name='PDF %',
                stackgroup='one',
                fillcolor='#1f77b4'
            ))
            fig_q9_stack.add_trace(go.Scatter(
                x=df_q9['MonthStart'],
                y=df_q9['WordPercent'],
                mode='lines',
                name='Word %',
                stackgroup='one',
                fillcolor='#ff7f0e'
            ))
            fig_q9_stack.add_trace(go.Scatter(
                x=df_q9['MonthStart'],
                y=df_q9['ExcelPercent'],
                mode='lines',
                name='Excel %',
                stackgroup='one',
                fillcolor='#2ca02c'
            ))
            fig_q9_stack.update_layout(
                title='Training Data: File Type Composition',
                xaxis_title='Month',
                yaxis_title='Percentage (%)',
                height=350,
                template='plotly_white',
                hovermode='x unified'
            )
            st.plotly_chart(fig_q9_stack, use_container_width=True)
        
        # Full training dataset table
        st.markdown("**Complete Training Dataset (13 Features)**")
        
        display_q9 = df_q9.copy()
        display_q9['MonthStart'] = display_q9['MonthStart'].dt.strftime('%Y-%m')
        
        # Select columns for display
        display_cols = [
            'MonthStart', 'FilesArchivedCount', 'VolumeGBArchived', 'StorageSavedGB',
            'ActiveTenants', 'ActiveSites', 'PDFPercent', 'WordPercent', 'ExcelPercent',
            'FilesWithErrors'
        ]
        display_df = display_q9[display_cols].copy()
        display_df = display_df.round(2)
        display_df.columns = [
            'Month', 'Files', 'Volume (GB)', 'Saved (GB)', 'Tenants', 'Sites',
            'PDF %', 'Word %', 'Excel %', 'Errors'
        ]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Download full dataset
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Training Dataset (CSV)",
            data=csv,
            file_name=f"training_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Summary statistics
        st.markdown("**Dataset Summary Statistics**")
        summary = pd.DataFrame({
            'Feature': [
                'Files Archived', 'Volume (GB)', 'Storage Saved (GB)',
                'Active Tenants', 'Active Sites', 'PDF %', 'Word %', 'Excel %'
            ],
            'Min': [
                df_q9['FilesArchivedCount'].min(),
                df_q9['VolumeGBArchived'].min(),
                df_q9['StorageSavedGB'].min(),
                df_q9['ActiveTenants'].min(),
                df_q9['ActiveSites'].min(),
                df_q9['PDFPercent'].min(),
                df_q9['WordPercent'].min(),
                df_q9['ExcelPercent'].min(),
            ],
            'Mean': [
                df_q9['FilesArchivedCount'].mean(),
                df_q9['VolumeGBArchived'].mean(),
                df_q9['StorageSavedGB'].mean(),
                df_q9['ActiveTenants'].mean(),
                df_q9['ActiveSites'].mean(),
                df_q9['PDFPercent'].mean(),
                df_q9['WordPercent'].mean(),
                df_q9['ExcelPercent'].mean(),
            ],
            'Max': [
                df_q9['FilesArchivedCount'].max(),
                df_q9['VolumeGBArchived'].max(),
                df_q9['StorageSavedGB'].max(),
                df_q9['ActiveTenants'].max(),
                df_q9['ActiveSites'].max(),
                df_q9['PDFPercent'].max(),
                df_q9['WordPercent'].max(),
                df_q9['ExcelPercent'].max(),
            ]
        })
        summary = summary.round(2)
        st.dataframe(summary, use_container_width=True, hide_index=True)


def main():
    """Main dashboard function"""
    
    # Load filters
    filters = load_sidebar()
    
    # Create header
    create_header()
    
    st.divider()
    
    # Create main tabs for different views
    tab_forecast, tab_analysis, tab_exploration, tab_monitoring, tab_feedback, tab_retraining, tab_cost = st.tabs([
        "📊 Forecast & Predictions",
        "📈 Analysis",
        "🔍 Data Exploration",
        "🔍 Monitoring",
        "📝 Feedback",
        "🔄 Retraining",
        "💳 Cost Monitoring"
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
    
    # TAB 3: Data Exploration (Queries 1-9)
    with tab_exploration:
        create_exploration_dashboard()
    
    # TAB 4: Monitoring Dashboard
    with tab_monitoring:
        if MONITORING_AVAILABLE:
            create_monitoring_dashboard()
        else:
            st.warning("⚠️ Monitoring dashboard is not available. Install required dependencies.")
            st.info("To enable monitoring, ensure the monitoring module is properly configured.")
    
    # TAB 5: Feedback Collection
    with tab_feedback:
        create_feedback_section()
    
    # TAB 6: Retraining Status
    with tab_retraining:
        create_retraining_status_section()
    
    # TAB 7: Cost Monitoring
    with tab_cost:
        if COST_MONITORING_AVAILABLE:
            create_cost_monitoring_dashboard()
        else:
            st.warning("⚠️ Cost monitoring module is not available. Install required dependencies.")
            st.info("To enable cost monitoring, ensure cost_monitoring.py is in the src/ui/ directory.")
    
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

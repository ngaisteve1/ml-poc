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

# Import monitoring dashboard
try:
    from monitoring_dashboard import create_monitoring_dashboard
    MONITORING_AVAILABLE = True
except ImportError as e:
    MONITORING_AVAILABLE = False
    import warnings
    warnings.warn(f"Monitoring dashboard not available: {e}")

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
    tab_forecast, tab_analysis, tab_monitoring = st.tabs([
        "📊 Forecast & Predictions",
        "📈 Analysis",
        "🔍 Monitoring"
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

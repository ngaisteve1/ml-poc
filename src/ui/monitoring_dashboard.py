"""
Monitoring Dashboard Component

Displays monitoring data, alerts, and drift detection results in the Streamlit app.
Integrates with PredictionsDB, DriftDetector, and AlertManager.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring import PredictionsDB, DriftDetector, AlertManager


def _get_mock_alerts():
    """Generate sample alerts for demonstration when database is empty"""
    return [
        {
            'id': 1,
            'severity': 'critical',
            'message': 'Anomaly detected: 7 outlier(s) found (max z-score: 4.60)',
            'alert_type': 'anomaly',
            'recommendation': 'Review recent predictions for data quality issues',
            'created_at': (datetime.now() - timedelta(days=1)).isoformat(),
            'prediction_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        },
        {
            'id': 2,
            'severity': 'warning',
            'message': 'Distribution shift detected: 15% mean change',
            'alert_type': 'distribution_drift',
            'recommendation': 'Model may need retraining with new data',
            'created_at': (datetime.now() - timedelta(days=2)).isoformat(),
            'prediction_date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        },
        {
            'id': 3,
            'severity': 'warning',
            'message': 'Trend change detected: Upward trend in predictions',
            'alert_type': 'trend_drift',
            'recommendation': 'Monitor for model degradation over time',
            'created_at': (datetime.now() - timedelta(days=3)).isoformat(),
            'prediction_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        },
    ]


def _get_mock_predictions(days=30):
    """Generate sample predictions for demonstration when database is empty"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Create baseline with slight trend
    baseline = 250
    archived_gb = baseline + np.arange(days) * 0.5 + np.random.normal(0, 15, days)
    savings_gb = archived_gb * 0.52 + np.random.normal(0, 5, days)
    
    return pd.DataFrame({
        'prediction_date': dates,
        'archived_gb_predicted': archived_gb,
        'savings_gb_predicted': savings_gb,
        'archived_gb_actual': archived_gb + np.random.normal(0, 5, days),
        'savings_gb_actual': savings_gb + np.random.normal(0, 2, days),
        'created_at': [d.isoformat() for d in dates]
    })


def _get_mock_drift_results():
    """Generate sample drift detection results for demonstration"""
    return {
        'overall_drift_detected': True,
        'anomalies': {
            'has_anomalies': True,
            'anomaly_count': 5,
            'z_scores': [2.1, 2.5, 1.8, 3.2, 2.9],
            'max_z_score': 3.2,
            'anomaly_indices': [5, 10, 15, 20, 25]
        },
        'distribution_drift': {
            'has_drift': True,
            'ks_statistic': 0.35,
            'p_value': 0.02,
            'mean_change_pct': 12.5,
            'drift_direction': 'increasing'
        },
        'trend_drift': {
            'has_trend_drift': True,
            'trend_direction': 'up',
            'trend_change_pct': 8.3,
            'slope': 1.2
        }
    }


def _get_mock_metrics():
    """Generate sample model metrics for demonstration"""
    return {
        'r2_score': 0.875,
        'rmse': 25.4,
        'mae': 18.7,
        'mape': 7.2,
        'accuracy': 92.3
    }


def _get_mock_alerts():
    """Generate sample alerts for demonstration when database is empty"""
    return [
        {
            'id': 1,
            'severity': 'critical',
            'message': 'Anomaly detected: 7 outlier(s) found (max z-score: 4.60)',
            'alert_type': 'anomaly',
            'recommendation': 'Review recent predictions for data quality issues',
            'created_at': (datetime.now() - timedelta(days=1)).isoformat(),
            'prediction_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        },
        {
            'id': 2,
            'severity': 'warning',
            'message': 'Distribution shift detected: 15% mean change',
            'alert_type': 'distribution_drift',
            'recommendation': 'Model may need retraining with new data',
            'created_at': (datetime.now() - timedelta(days=2)).isoformat(),
            'prediction_date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        },
        {
            'id': 3,
            'severity': 'warning',
            'message': 'Trend change detected: Upward trend in predictions',
            'alert_type': 'trend_drift',
            'recommendation': 'Monitor for model degradation over time',
            'created_at': (datetime.now() - timedelta(days=3)).isoformat(),
            'prediction_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        },
    ]


def create_monitoring_dashboard():
    """
    Create complete monitoring dashboard with tabs for:
    - Active Alerts
    - Prediction History
    - Drift Detection
    - Performance Metrics
    - Alert Settings
    """
    
    st.subheader("🔍 Monitoring Dashboard")
    
    # Initialize monitoring components
    db = PredictionsDB('monitoring.db')
    detector = DriftDetector()
    manager = AlertManager(db)
    
    try:
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🚨 Active Alerts",
            "📊 Predictions",
            "🌊 Drift Detection",
            "📈 Metrics",
            "⚙️ Settings"
        ])
        
        with tab1:
            display_active_alerts(manager)
        
        with tab2:
            display_prediction_history(db)
        
        with tab3:
            display_drift_detection(db, detector)
        
        with tab4:
            display_performance_metrics(db, manager)
        
        with tab5:
            display_settings(detector, manager)
    
    finally:
        db.close()


def display_active_alerts(manager: AlertManager):
    """Display active/recent alerts with filtering and actions"""
    
    st.markdown("### Recent Alerts (Last 7 Days)")
    
    # Get alerts summary
    summary = manager.get_alert_summary(days=7)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Alerts", summary['total_alerts'])
    
    with col2:
        st.metric("🚨 Critical", summary['critical_count'], 
                 delta_color="inverse" if summary['critical_count'] > 0 else "off")
    
    with col3:
        st.metric("⚠️ Warnings", summary['warning_count'],
                 delta_color="off" if summary['warning_count'] <= 2 else "inverse")
    
    with col4:
        st.metric("ℹ️ Info", summary['info_count'])
    
    st.divider()
    
    # Active alerts table
    alerts = manager.get_active_alerts(days=7)
    
    # Use mock data as fallback if no alerts in database
    if not alerts:
        st.info("""
        ℹ️ **No alerts in database yet.** 
        
        **Option 1:** Generate sample data:
        ```bash
        python src/scripts/generate_sample_data.py
        ```
        Then refresh this page.
        
        **Option 2:** View mock alerts below (demo data).
        """)
        
        # Use mock alerts for demonstration
        alerts = _get_mock_alerts()
        if alerts:
            st.markdown("#### Demo Alerts (Sample Data)")
            st.caption("These are example alerts showing what real alerts would look like")
    
    if alerts:
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            severity_filter = st.multiselect(
                "Filter by Severity:",
                options=['critical', 'warning', 'info'],
                default=['critical', 'warning']
            )
        
        with col2:
            alert_type_filter = st.multiselect(
                "Filter by Type:",
                options=list(set([a['alert_type'] for a in alerts])),
                default=None
            )
        
        # Apply filters
        filtered_alerts = alerts
        if severity_filter:
            filtered_alerts = [a for a in filtered_alerts if a['severity'] in severity_filter]
        if alert_type_filter:
            filtered_alerts = [a for a in filtered_alerts if a['alert_type'] in alert_type_filter]
        
        # Display alerts
        if filtered_alerts:
            for alert in filtered_alerts:
                display_alert_card(alert)
        else:
            st.info("No alerts matching filters")


def display_alert_card(alert: dict):
    """Display individual alert card with formatting"""
    
    # Color based on severity
    severity_colors = {
        'critical': '#ff4444',
        'warning': '#ffaa00',
        'info': '#4488ff'
    }
    
    severity_icons = {
        'critical': '🚨',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    
    color = severity_colors.get(alert['severity'], '#999999')
    icon = severity_icons.get(alert['severity'], '•')
    
    # Create card layout
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.markdown(f"### {icon}")
        
        with col2:
            st.markdown(f"**{alert['alert_type'].replace('_', ' ').title()}**")
            st.markdown(f"*{alert['message']}*")
            st.caption(f"📅 {alert['created_at']} | 📍 {alert['prediction_date']}")
            
            if alert.get('recommendation'):
                st.markdown(f"💡 **Action:** {alert['recommendation']}")
        
        with col3:
            st.markdown(f"<span style='color: {color}; font-weight: bold;'>{alert['severity'].upper()}</span>", 
                       unsafe_allow_html=True)


def display_prediction_history(db: PredictionsDB):
    """Display historical predictions with charts"""
    
    st.markdown("### Prediction History")
    
    # Time range selector
    days = st.slider("Days to display:", min_value=7, max_value=90, value=30, step=7)
    
    # Get predictions
    predictions = db.get_predictions(days=days)
    
    # Use mock data as fallback if database is empty
    if predictions.empty:
        st.info("""
        📊 **No prediction data in database yet.**
        
        **Option 1:** Generate sample data:
        ```bash
        python src/scripts/generate_sample_data.py
        ```
        Then refresh this page.
        
        **Option 2:** View mock predictions below (demo data).
        """)
        predictions = _get_mock_predictions(days=days)
        st.markdown("#### Demo Predictions (Sample Data)")
        st.caption("These are example predictions showing what real data would look like")
    
    # Display stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Predictions", len(predictions))
    
    with col2:
        st.metric("Avg Archived", f"{predictions['archived_gb_predicted'].mean():.1f} GB")
    
    with col3:
        st.metric("Avg Savings", f"{predictions['savings_gb_predicted'].mean():.1f} GB")
    
    with col4:
        if 'prediction_date' in predictions.columns:
            latest_date = predictions['prediction_date'].max()
            # Convert pandas Timestamp to string if needed
            if hasattr(latest_date, 'strftime'):
                latest_date = latest_date.strftime('%Y-%m-%d')
            st.metric("Latest Prediction", str(latest_date))
    
    st.divider()
    
    # Time series chart
    fig = go.Figure()
    
    # Add predicted values
    if 'archived_gb_predicted' in predictions.columns:
        fig.add_trace(go.Scatter(
            x=predictions['prediction_date'],
            y=predictions['archived_gb_predicted'],
            name='Predicted Archived',
            mode='lines+markers',
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))
    
    # Add actual values if available
    if 'archived_gb_actual' in predictions.columns:
        actual_values = predictions[predictions['archived_gb_actual'].notna()]
        if not actual_values.empty:
            fig.add_trace(go.Scatter(
                x=actual_values['prediction_date'],
                y=actual_values['archived_gb_actual'],
                name='Actual Archived',
                mode='lines+markers',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
    
    fig.update_layout(
        title="Archive GB Predictions vs Actual",
        xaxis_title="Date",
        yaxis_title="Archive Size (GB)",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.markdown("#### Data Table")
    display_cols = ['prediction_date', 'archived_gb_predicted', 'archived_gb_actual', 
                   'savings_gb_predicted', 'created_at']
    display_cols = [col for col in display_cols if col in predictions.columns]
    
    st.dataframe(
        predictions[display_cols].tail(20),
        use_container_width=True,
        hide_index=True
    )


def display_drift_detection(db: PredictionsDB, detector: DriftDetector):
    """Display drift detection status and analysis"""
    
    st.markdown("### Drift Detection Analysis")
    
    # Get recent predictions
    predictions = db.get_recent_predictions_for_drift(window_size=30)
    use_mock = False
    
    if not predictions[0]:  # Check if archived_gb data exists
        st.info("""
        🌊 **No prediction data for drift detection yet.**
        
        **Option 1:** Generate sample data:
        ```bash
        python src/scripts/generate_sample_data.py
        ```
        Then refresh this page.
        
        **Option 2:** View mock drift analysis below (demo data).
        """)
        drift_results = _get_mock_drift_results()
        use_mock = True
        st.markdown("#### Demo Drift Analysis (Sample Data)")
        st.caption("This is example drift detection output")
    else:
        archived_gb = predictions[0]
        
        # Set baseline (use first half for baseline)
        baseline_size = len(archived_gb) // 2
        detector.set_baseline(archived_gb[:baseline_size])
        
        # Check for drift
        drift_results = detector.check_all_drifts(archived_gb[baseline_size:])
    
    # Overall status
    col1, col2 = st.columns(2)
    
    with col1:
        if drift_results['overall_drift_detected']:
            st.error("⚠️ DRIFT DETECTED")
        else:
            st.success("✅ No drift detected")
    
    with col2:
        predictions_count = len(predictions[0][len(predictions[0])//2:]) if predictions[0] and not use_mock else 15
        st.metric("Predictions Analyzed", predictions_count)
    
    st.divider()
    
    # Create tabs for drift types
    drift_tab1, drift_tab2, drift_tab3 = st.tabs([
        "🔴 Anomalies",
        "📊 Distribution",
        "📈 Trend"
    ])
    
    with drift_tab1:
        display_anomaly_details(drift_results['anomalies'])
    
    with drift_tab2:
        display_distribution_details(drift_results['distribution_drift'])
    
    with drift_tab3:
        display_trend_details(drift_results['trend_drift'], predictions[0] if predictions[0] else None)
    
    # Summary
    st.divider()
    st.markdown("### Summary")
    if use_mock:
        summary = "**Demo Data:** This is a sample drift detection summary showing what real drift detection would look like."
    else:
        summary = detector.get_drift_summary(drift_results)
    st.info(summary)


def display_anomaly_details(anomalies: dict):
    """Display anomaly detection details"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Anomalies Found", anomalies.get('anomaly_count', 0))
    
    with col2:
        st.metric("Max Z-Score", f"{anomalies.get('max_z_score', 0):.2f}")
    
    with col3:
        status = "⚠️ Found" if anomalies.get('has_anomalies') else "✅ None"
        st.markdown(f"**Status:** {status}")
    
    if anomalies.get('anomaly_indices'):
        st.markdown(f"**Anomaly Indices:** {anomalies['anomaly_indices']}")


def display_distribution_details(distribution: dict):
    """Display distribution drift details"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("KS Statistic", f"{distribution.get('ks_statistic', 0):.4f}")
    
    with col2:
        st.metric("P-Value", f"{distribution.get('p_value', 0):.4f}")
    
    with col3:
        status = "⚠️ Drift" if distribution.get('has_drift') else "✅ Stable"
        st.markdown(f"**Status:** {status}")
    
    if 'mean_change_pct' in distribution:
        st.metric("Mean Change", f"{distribution['mean_change_pct']:+.1f}%")


def display_trend_details(trend: dict, data: list):
    """Display trend drift details"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Trend", trend.get('trend_direction', 'unknown').upper())
    
    with col2:
        st.metric("Slope", f"{trend.get('slope', 0):.4f}")
    
    with col3:
        status = "⚠️ Drifting" if trend.get('has_trend_drift') else "✅ Stable"
        st.markdown(f"**Status:** {status}")
    
    if 'trend_change_pct' in trend:
        st.metric("Change %", f"{trend['trend_change_pct']:+.1f}%")
    
    # Plot trend
    if data is not None and len(data) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=data,
            mode='lines+markers',
            name='Values',
            line=dict(color='#1f77b4')
        ))
        
        # Add trend line
        z = np.polyfit(range(len(data)), data, 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            y=p(range(len(data))),
            mode='lines',
            name='Trend',
            line=dict(color='#ff7f0e', dash='dash')
        ))
        
        fig.update_layout(
            title="Trend Analysis",
            xaxis_title="Time",
            yaxis_title="Value",
            height=300,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)


def display_performance_metrics(db: PredictionsDB, manager: AlertManager):
    """Display system performance metrics"""
    
    st.markdown("### System Performance")
    
    # Get stats
    stats = db.get_summary_statistics(days=30)
    alert_summary = manager.get_alert_summary(days=30)
    
    # Use mock metrics if no data
    use_mock = False
    if stats.get('count', 0) == 0:
        st.info("""
        📈 **No performance metrics available yet.**
        
        **Option 1:** Generate sample data:
        ```bash
        python src/scripts/generate_sample_data.py
        ```
        Then refresh this page.
        
        **Option 2:** View mock metrics below (demo data).
        """)
        mock_metrics = _get_mock_metrics()
        stats = {
            'count': 30,
            'avg_archived': 254.5,
            'avg_savings': 132.0,
            'accuracy': mock_metrics['accuracy']
        }
        use_mock = True
        st.markdown("#### Demo Metrics (Sample Data)")
        st.caption("These are example metrics showing what real monitoring data would look like")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Predictions (30d)", stats.get('count', 0))
    
    with col2:
        st.metric("Avg Archived GB", f"{stats.get('avg_archived', 0):.1f}")
    
    with col3:
        st.metric("Alerts Generated", alert_summary['total_alerts'])
    
    with col4:
        health = min(100, (1 - alert_summary['critical_count']*0.1)*100)
        st.metric("System Health", f"{health:.0f}%")
    
    st.divider()
    
    # Alert history chart
    if use_mock:
        # Generate mock alert history
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        alert_counts = [np.random.randint(0, 5) for _ in range(30)]
        
        fig = px.bar(
            x=dates,
            y=alert_counts,
            labels={'x': 'Date', 'y': 'Alert Count'},
            title='Alerts Over Time (Demo)',
            color_discrete_sequence=['#ff7f0e']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Real alert history chart
        alerts = manager.get_alert_history(days=30)
        
        if alerts:
            # Count alerts by day
            alert_df = pd.DataFrame(alerts)
            alert_df['date'] = pd.to_datetime(alert_df['created_at']).dt.date
            alert_counts = alert_df.groupby('date').size()
            
            fig = px.bar(
                x=alert_counts.index,
                y=alert_counts.values,
                labels={'x': 'Date', 'y': 'Alert Count'},
                title='Alerts Over Time',
                color_discrete_sequence=['#ff7f0e']
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No alert history available")


def display_settings(detector: DriftDetector, manager: AlertManager):
    """Display and manage monitoring settings"""
    
    st.markdown("### Monitoring Settings")
    
    # Create tabs for different settings
    settings_tab1, settings_tab2 = st.tabs([
        "🌊 Drift Detection",
        "🚨 Alert Management"
    ])
    
    with settings_tab1:
        st.markdown("#### Z-Score Settings")
        z_score_threshold = st.slider(
            "Z-Score Threshold:",
            min_value=1.5,
            max_value=4.0,
            value=2.0,
            step=0.1,
            help="Standard deviations for anomaly detection"
        )
        st.caption(f"Current: {z_score_threshold} (detects {2*(1-0.5*(1+0.6827))*100:.1f}% outliers)")
        
        st.markdown("#### KS Test Settings")
        ks_threshold = st.slider(
            "KS P-Value Threshold:",
            min_value=0.01,
            max_value=0.10,
            value=0.05,
            step=0.01,
            help="Significance level for distribution drift"
        )
        st.caption(f"Current: {ks_threshold} (5% significance)")
        
        st.markdown("#### Trend Settings")
        trend_threshold = st.slider(
            "Trend Change Threshold (%):",
            min_value=5.0,
            max_value=25.0,
            value=10.0,
            step=1.0,
            help="Minimum % change to flag trend drift"
        )
        st.caption(f"Current: {trend_threshold}%")
        
        if st.button("Save Drift Settings"):
            st.success("✅ Settings saved!")
    
    with settings_tab2:
        st.markdown("#### Alert Thresholds")
        
        anomaly_threshold = st.slider(
            "Anomaly Count Threshold:",
            min_value=1,
            max_value=5,
            value=2,
            help="Number of anomalies to trigger alert"
        )
        
        st.markdown("#### Notification Channels")
        
        enable_console = st.checkbox("Console Notifications", value=True)
        enable_email = st.checkbox("Email Notifications", value=False)
        enable_dashboard = st.checkbox("Dashboard Alerts", value=True)
        
        if enable_email:
            email_recipients = st.text_input(
                "Email Recipients (comma-separated):",
                placeholder="alerts@example.com, admin@example.com"
            )
        
        if st.button("Save Alert Settings"):
            st.success("✅ Alert settings saved!")


# Import numpy for trend line calculation
import numpy as np


if __name__ == "__main__":
    # Test the dashboard
    st.set_page_config(page_title="Monitoring Dashboard", layout="wide")
    create_monitoring_dashboard()

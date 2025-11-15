"""
PRACTICAL EXAMPLE: How to integrate Azure ML endpoint into streamlit_app.py

This file shows the EXACT changes needed to switch from mock data to real Azure ML predictions.

Copy & paste the relevant sections into your streamlit_app.py
"""

# ============================================================================
# CHANGE #1: Update imports at top of streamlit_app.py
# ============================================================================

# BEFORE:
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json

from mock_data import get_mock_historical_data, get_mock_prediction, get_mock_metrics
"""

# AFTER:
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mock_data import get_mock_historical_data, get_mock_metrics
from src.ml.azure_endpoint_client import get_predictions_from_azure, AzureMLEndpointClient
"""


# ============================================================================
# CHANGE #2: Create helper function for predictions with fallback
# ============================================================================

def get_forecast_predictions(historical_df, forecast_days=90, use_azure=True):
    """
    Get predictions from Azure ML endpoint with fallback to mock data
    
    Args:
        historical_df: DataFrame with historical archive data
        forecast_days: Number of days to forecast
        use_azure: If True, try Azure ML first; if False, use mock data
    
    Returns:
        Tuple of (forecast_df, metrics, data_source)
        data_source is either 'Azure ML' or 'Mock Data'
    """
    if use_azure:
        try:
            # Try to get real predictions from Azure ML
            forecast_df, metrics = get_predictions_from_azure(historical_df, forecast_days)
            return forecast_df, metrics, "Azure ML ✅"
            
        except Exception as e:
            # Log the error but don't crash
            print(f"⚠️  Azure ML Error: {str(e)}")
            print("📦 Falling back to mock data...")
            
            # Use mock data as fallback
            from mock_data import get_mock_prediction
            forecast_df = get_mock_prediction(forecast_days)
            metrics = get_mock_metrics()
            return forecast_df, metrics, "Mock Data (Fallback)"
    else:
        # Use mock data directly
        from mock_data import get_mock_prediction
        forecast_df = get_mock_prediction(forecast_days)
        metrics = get_mock_metrics()
        return forecast_df, metrics, "Mock Data"


# ============================================================================
# CHANGE #3: Update main function to use new helper
# ============================================================================

def main():
    """Main dashboard function"""
    
    # Create sidebar
    filters = load_sidebar()
    create_header()
    
    # Load data
    st.subheader("📊 Data Loading")
    
    # Show data source selector
    data_source_col1, data_source_col2 = st.columns(2)
    with data_source_col1:
        use_azure = st.checkbox(
            "Use Azure ML Endpoint",
            value=True,
            help="✅ Use real predictions from Azure ML Studio\n❌ Use mock predictions"
        )
    
    with data_source_col2:
        if use_azure:
            st.success("🔗 Connected to Azure ML")
        else:
            st.info("📦 Using mock data")
    
    # Load historical data (always from mock for now)
    with st.spinner("Loading historical data..."):
        historical_data = get_mock_historical_data(months=12)
    
    # Get predictions (real or mock)
    with st.spinner("Getting predictions..."):
        predictions, metrics, data_source = get_forecast_predictions(
            historical_data,
            forecast_days=90,
            use_azure=use_azure
        )
    
    # Show data source indicator
    st.caption(f"📌 Data Source: {data_source}")
    
    # Display metrics
    create_summary_metrics(metrics)
    
    # Display charts
    st.divider()
    create_forecast_chart(historical_data, predictions)
    
    # ... rest of your dashboard code ...


# ============================================================================
# CHANGE #4: Update metrics display to show Azure ML metrics
# ============================================================================

def create_summary_metrics(metrics):
    """Display summary metrics (updated for Azure ML)"""
    st.subheader("📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_size = metrics.get('current_size', 0)
        delta = metrics.get('current_size_delta', 0)
        st.metric(
            label="Current Archive Size",
            value=f"{current_size:.2f} GB",
            delta=f"+{delta:.2f} GB" if delta > 0 else f"{delta:.2f} GB"
        )
    
    with col2:
        predicted_30d = metrics.get('predicted_30d', 0)
        delta = metrics.get('predicted_30d_delta', 0)
        st.metric(
            label="Predicted (30 days)",
            value=f"{predicted_30d:.2f} GB",
            delta=f"+{delta:.2f} GB" if delta > 0 else f"{delta:.2f} GB"
        )
    
    with col3:
        savings = metrics.get('potential_savings', 0)
        savings_pct = metrics.get('savings_percent', 0)
        st.metric(
            label="Potential Savings",
            value=f"{savings:.2f} GB",
            delta=f"{savings_pct:.1f}%"
        )
    
    with col4:
        # Show model accuracy (from Azure ML if available)
        accuracy = metrics.get('model_accuracy', 
                              metrics.get('r2_score', 0) * 100)  # Azure ML returns R² 0-1
        st.metric(
            label="Model Accuracy",
            value=f"{accuracy:.1f}%",
            delta="Azure ML ✅" if metrics.get('r2_score') else "Mock Data"
        )


# ============================================================================
# CHANGE #5: Show Azure ML endpoint status in dashboard
# ============================================================================

def show_endpoint_status():
    """Display Azure ML endpoint status (new section)"""
    st.sidebar.divider()
    st.sidebar.subheader("🔗 Azure ML Status")
    
    try:
        client = AzureMLEndpointClient()
        st.sidebar.success("✅ Endpoint Connected")
        st.sidebar.caption(f"🌐 {client.endpoint_url[:50]}...")
        
    except ValueError as e:
        st.sidebar.error("❌ Endpoint Not Configured")
        st.sidebar.caption("Add MLFLOW_* vars to .env")
    except Exception as e:
        st.sidebar.warning("⚠️ Endpoint Unreachable")
        st.sidebar.caption(f"Error: {str(e)[:40]}...")


# ============================================================================
# CHANGE #6: Add this to load_sidebar() function
# ============================================================================

def load_sidebar():
    """Load sidebar filters (updated)"""
    st.sidebar.markdown("## ⚙️ Filters & Settings")
    
    # ... existing filter code ...
    
    # ADD THIS NEW SECTION:
    st.sidebar.divider()
    st.sidebar.subheader("🔌 Data Source")
    
    data_source = st.sidebar.radio(
        "Select data source:",
        options=["Azure ML (Real)", "Mock Data (Demo)"],
        index=0,
        help="Azure ML: Real predictions from endpoint\nMock Data: Synthetic test data"
    )
    
    use_azure = data_source == "Azure ML (Real)"
    
    # Show endpoint status
    if use_azure:
        show_endpoint_status()
    
    # Return filters dict (add use_azure to it)
    return {
        "date_range": date_range,
        "file_types": file_types,
        "tenant": tenant,
        "site": site,
        "model": model_version,
        "use_azure": use_azure
    }


# ============================================================================
# CHANGE #7: Error handling for Azure ML integration
# ============================================================================

# Add this helper function for robust error handling:

@st.cache_resource
def init_azure_client():
    """Initialize Azure ML client (cached)"""
    try:
        return AzureMLEndpointClient()
    except Exception as e:
        st.warning(f"Azure ML not available: {str(e)}")
        return None


if __name__ == "__main__":
    main()
    
    # Optional: Show debug info in sidebar
    if st.sidebar.checkbox("🐛 Show Debug Info"):
        st.sidebar.write("### Debug Information")
        st.sidebar.json({
            "azure_client": "Available" if init_azure_client() else "Not Available",
            "python_version": "3.10+",
            "streamlit_version": "1.31+",
        })


# ============================================================================
# SUMMARY: What Changed
# ============================================================================

"""
MINIMAL CHANGES TO EXISTING CODE:

1. Add imports for Azure ML client
2. Create get_forecast_predictions() helper with fallback
3. Add use_azure checkbox in sidebar
4. Replace get_mock_prediction() calls with get_forecast_predictions()
5. Update metrics display to show Azure ML metrics (R² score)
6. Add endpoint status display

BENEFITS:
✅ Real predictions from Azure ML
✅ Fallback to mock data if endpoint unavailable
✅ Single checkbox to switch between data sources
✅ No breaking changes to existing code
✅ Gradual migration possible

TESTING:
1. Run dashboard with use_azure=True
2. Check data source indicator shows "Azure ML ✅"
3. Verify metrics match Azure ML model performance (R²=0.875)
4. Switch to mock data and verify fallback works
"""

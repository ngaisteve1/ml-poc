# 🔗 Azure ML Endpoint Integration Guide

## Overview

Your Azure ML endpoint can now provide **real predictions** instead of mock data. This guide explains how to integrate it into your Streamlit dashboard.

---

## 📋 What You Have

| Component | Status | Details |
|-----------|--------|---------|
| **Azure ML Workspace** | ✅ Configured | `mlflow-workspace` |
| **Endpoint** | ✅ Created | `smartarchive-archive-forecast-1` |
| **Endpoint URL** | ✅ Ready | `https://mlflow-workspace-qzgku.southeastasia.inference.ml.azure.com/score` |
| **API Key** | ✅ Set | In `.env` file |
| **Client Library** | ✅ New | `src/ml/azure_endpoint_client.py` |

---

## 🔄 How the Endpoint Works

### Request Format

```python
# Historical data (what you send)
historical_data = {
    "data": [
        [archived_gb, total_files, avg_file_size_mb],
        [archived_gb, total_files, avg_file_size_mb],
        ...
    ]
}

# Send to endpoint
POST https://mlflow-workspace-qzgku.southeastasia.inference.ml.azure.com/score
Header: Authorization: Bearer {API_KEY}
Body: historical_data (JSON)
```

### Response Format

```python
# Azure ML endpoint returns
{
    "predictions": [pred1, pred2, pred3, ...],
    "confidence_intervals": {
        "upper": [upper1, upper2, ...],
        "lower": [lower1, lower2, ...]
    },
    "metrics": {
        "r2": 0.875,
        "rmse": 2.5,
        "mae": 1.8,
        "mape": 3.2
    }
}
```

---

## 🚀 Integration Steps

### Step 1: Test the Endpoint Connection

```bash
cd ml-poc
python src/ml/azure_endpoint_client.py
```

**Expected output:**
```
Testing Azure ML Endpoint Connection...
------------------------------------------------------------
✅ Endpoint configured: https://mlflow-workspace-qzgku.southeastasia.inference.ml.azure.com/score

📊 Sample request with 90 historical records
Payload shape: 90 records × 3 features

🚀 Calling endpoint...
✅ Response received!
Response keys: ['predictions', 'confidence_intervals', 'metrics']
Model metrics: {'r2': 0.875, 'rmse': 2.5, ...}
```

### Step 2: Update Streamlit Dashboard

Replace mock predictions with real predictions in `src/ui/streamlit_app.py`:

**Before (using mock):**
```python
from mock_data import get_mock_prediction, get_mock_metrics

def main():
    st.title("Archive Forecast Dashboard")
    
    # Load mock data
    historical = get_mock_historical_data()
    forecast = get_mock_prediction()  # ❌ MOCK DATA
    metrics = get_mock_metrics()      # ❌ MOCK DATA
```

**After (using real Azure ML):**
```python
from src.ml.azure_endpoint_client import get_predictions_from_azure, get_model_metrics_from_azure
from mock_data import get_mock_historical_data

def main():
    st.title("Archive Forecast Dashboard")
    
    # Load historical data
    historical = get_mock_historical_data()  # Or real data source
    
    try:
        # Get REAL predictions from Azure ML
        forecast, metrics = get_predictions_from_azure(historical)  # ✅ REAL DATA
        
    except Exception as e:
        st.error(f"Azure ML Error: {str(e)}")
        st.info("Falling back to mock data...")
        forecast = get_mock_prediction()
        metrics = get_mock_metrics()
```

### Step 3: Handle Errors Gracefully

```python
import streamlit as st
from src.ml.azure_endpoint_client import AzureMLEndpointClient

@st.cache_resource
def get_azure_client():
    """Initialize Azure ML client with error handling"""
    try:
        return AzureMLEndpointClient()
    except ValueError as e:
        st.error(f"⚠️ Azure ML Configuration Error: {str(e)}")
        st.info("Add MLFLOW_ENDPOINT and MLFLOW_API_KEY to .env file")
        return None

def get_predictions(historical_df, use_azure=True):
    """Get predictions with fallback to mock data"""
    
    if use_azure:
        client = get_azure_client()
        if client:
            try:
                return client.get_predictions(historical_df, forecast_days=90)
            except Exception as e:
                st.warning(f"Endpoint error: {str(e)}. Using mock data.")
    
    # Fallback to mock
    from mock_data import get_mock_prediction
    return get_mock_prediction(), {}
```

---

## 📊 Payload Structure Explained

### Your Historical Data ➜ Endpoint Input

```python
# Your historical data from mock_data.py
historical_df:
    date            archived_gb  total_files  avg_file_size_mb
0   2025-08-16      500.5        5005000      1.20
1   2025-08-17      501.2        5012000      1.21
2   2025-08-18      502.1        5021000      1.22
...

# Converted to endpoint payload
{
    "data": [
        [500.5,  5005000,  1.20],
        [501.2,  5012000,  1.21],
        [502.1,  5021000,  1.22],
        ...
    ]
}
```

### What Features Mean

| Feature | Source | Range | Example |
|---------|--------|-------|---------|
| **archived_gb** | Current storage size | 0-∞ GB | 500-600 GB |
| **total_files** | Number of files | 0-∞ | 5M-6M files |
| **avg_file_size_mb** | Average file size | 0.5-10 MB | 1.2 MB |

---

## 🔐 Security Best Practices

### ✅ DO:
- Store API key in `.env` file (never in code)
- Use `load_dotenv()` to load it at runtime
- Rotate API key regularly
- Add API key to `.gitignore`

### ❌ DON'T:
- Commit `.env` file with real keys
- Log the full API key in output
- Use same key for dev/prod
- Hardcode endpoint URL

**Check .gitignore:**
```bash
# Ensure .env is ignored
cat .gitignore | grep ".env"
# Output should show: .env
```

---

## 📈 Example: Full Integration

### Replace entire prediction function:

**Old mock_data.py approach:**
```python
# src/ui/streamlit_app.py
from mock_data import get_mock_historical_data, get_mock_prediction

historical = get_mock_historical_data()
forecast = get_mock_prediction()
```

**New Azure ML approach:**
```python
# src/ui/streamlit_app.py
from src.ml.azure_endpoint_client import get_predictions_from_azure
from mock_data import get_mock_historical_data

historical = get_mock_historical_data()
forecast, metrics = get_predictions_from_azure(historical, forecast_days=90)

# Now forecast has:
# - date: prediction date
# - archived_gb: REAL prediction from model
# - confidence_upper: confidence interval upper bound
# - confidence_lower: confidence interval lower bound
# - metric_r2: model R² score
# - metric_rmse: model RMSE
```

---

## 🧪 Testing Checklist

- [ ] `.env` file has MLFLOW_ENDPOINT and MLFLOW_API_KEY
- [ ] Run `python src/ml/azure_endpoint_client.py` successfully
- [ ] No connection errors
- [ ] Response contains predictions and metrics
- [ ] Update Streamlit to call endpoint instead of mock_data
- [ ] Dashboard displays real predictions
- [ ] Metrics show actual model performance (R²=0.875, etc.)
- [ ] Charts update with real forecast data

---

## 🐛 Troubleshooting

### Error: "Authentication failed. Check MLFLOW_API_KEY"
**Solution:** 
- Verify API key in Azure ML Studio → Endpoints → smartarchive-archive-forecast-1 → Consume
- Update `.env` file with correct key

### Error: "Endpoint not found"
**Solution:**
- Check endpoint URL in Azure ML Studio
- Verify endpoint is in "Succeeded" state
- Update `.env` with correct URL

### Error: "Timeout (30s)"
**Solution:**
- Endpoint might be slow (cold start)
- Try again - Azure instances may need time to warm up
- Check endpoint status in Azure portal

### Error: "ModuleNotFoundError: No module named 'requests'"
**Solution:**
```bash
pip install requests
# Or update requirements.txt:
pip install -r requirements.txt
```

---

## 📚 Additional Resources

| File | Purpose |
|------|---------|
| `src/ml/azure_endpoint_client.py` | Main endpoint client |
| `.env` | Endpoint credentials |
| `docs/AZURE_ENDPOINT_INTEGRATION.md` | This guide |

---

## 🎯 Next Steps

1. **Test the connection:** `python src/ml/azure_endpoint_client.py`
2. **Integrate into Streamlit:** Update `src/ui/streamlit_app.py`
3. **Run dashboard:** `streamlit run src/ui/streamlit_app.py`
4. **Verify metrics:** Check that dashboard shows real R² score (0.875)

---

## Questions?

Check the inline comments in `src/ml/azure_endpoint_client.py` for detailed explanations of each function.

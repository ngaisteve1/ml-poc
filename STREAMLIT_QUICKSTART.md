# 🎯 Streamlit UI - Quick Start Guide

## Setup

### Don't switch environments. Stay in your current Anaconda env and just add Streamlit/Plotly to it

### 1. Install Dependencies

```bash
# Install Streamlit and visualization libraries
pip install streamlit plotly
pip install streamlit==1.31.1 plotly==5.18.0
```

Or update your existing environment:
```bash
pip install --upgrade streamlit plotly
```

### 2. Run the Dashboard

```bash
# Navigate to ml-poc directory
cd ml-poc

# Start the Streamlit app
streamlit run src/ui/streamlit_app.py
```

The dashboard will automatically open in your browser at: **http://localhost:8501**

---

## Dashboard Overview

### 🎨 Main Components

#### 1. **Sidebar Filters**
- 📅 Date Range selector
- 📁 File type filter (PDF, DOCX, XLSX, Other)
- 🏢 Tenant selector
- 📍 Site selector
- 🤖 Model version selector

#### 2. **Summary Metrics** (Top of page)
- Current Archive Size (GB)
- Predicted Size (30 days)
- Potential Savings (GB)
- Model Accuracy (%)

#### 3. **Analysis & Trends**
- **Historical vs Predicted**: Time series with confidence intervals
- **File Type Distribution**: Pie chart showing file type breakdown

#### 4. **Savings Projection**
- Monthly savings breakdown (bar chart)
- Cumulative savings over time (line chart)

#### 5. **Scenario Simulator**
Interactive tool to test different strategies:
- Archive Frequency (files/day)
- Average File Size (MB)
- Retention Period (days)

Shows simulated impact on:
- Projected archive size
- Monthly growth
- Yearly projection

#### 6. **Model Performance**
- Accuracy metrics (R², RMSE, MAE, MAPE)
- Model information (type, features, training data, update date)

#### 7. **Data Export**
- Detailed predictions table
- Download as CSV button

---

## Features

✅ **Interactive Charts**
- Hover for details
- Zoom and pan
- Download as PNG

✅ **Real-time Filtering**
- Change filters and see results update instantly

✅ **Scenario Simulation**
- Test different "what-if" scenarios
- See impact on predictions

✅ **Data Export**
- Download predictions as CSV
- Compatible with Excel, Python, R, etc.

✅ **Responsive Design**
- Works on desktop and tablet
- Clean, professional UI

---

## Mock Data

The dashboard currently uses **mock data** for testing. This allows you to:
- See how the UI works
- Test different features
- Plan real data integration


### To Use the CSV Data from test_data folder

Edit `src/ui/mock_data.py`:

```python
def get_mock_historical_data(months=12):
    # Instead of generating mock data:
    df = pd.read_csv('test_data/archive-data.csv')  # or your real data file
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date').tail(365)  # Last 12 months

def get_mock_prediction(days=90):
    # Load real historical and use your trained model
    df = pd.read_csv('test_data/archive-data.csv')
    # Then run through your ML pipeline
    return predictions_df
```    

### To Use Real Data from SQL

Edit `src/ui/mock_data.py`:

```python
def get_mock_historical_data(months=12):
    # Replace with your actual database query
    # Example: df = pd.read_sql(query, connection)
    return df
```

---

## Troubleshooting

### Port Already in Use
```bash
# Use a different port
streamlit run src/ui/streamlit_app.py --server.port 8502
```

### Missing Dependencies
```bash
# Reinstall all required packages
pip install --upgrade streamlit plotly pandas numpy
```

### Slow Performance
- Check your network connection
- Reduce date range in filters
- Clear browser cache

### Charts Not Showing
- Ensure Plotly is installed: `pip install plotly`
- Refresh the browser
- Check browser console for errors

---

## Next Steps

### 🟨 Current Status: **Successful (Baseline)**
- ✅ Model trains and predicts
- ✅ UI runs and displays predictions
- ✅ Interactive features working
- ⚠️ Uses mock data

### 🟩 To Reach **Excellent**:
1. **Connect Real Data** (1 week)
   - Query SmartArchive database
   - Update `mock_data.py` functions
   - Validate data quality

2. **Add More Filters** (3-5 days)
   - Add date range selector
   - Filter by archive status
   - Add export formats (PDF, Excel)

3. **Deploy to Cloud** (3-5 days)
   - Deploy to Streamlit Cloud or Azure
   - Add authentication
   - Setup monitoring

---

## File Structure

```
ml-poc/
├── src/ui/
│   ├── __init__.py                  # Package marker
│   ├── streamlit_app.py             # Main dashboard app
│   ├── mock_data.py                 # Mock data generation
│   ├── README.md                    # UI documentation
│   └── STREAMLIT_QUICKSTART.md      # This file
├── requirements.txt                  # Python dependencies
└── ...
```

---

## API Integration (Future)

When you deploy the Azure ML endpoint, integrate it:

```python
# In streamlit_app.py
import requests

def get_prediction_from_api(input_data):
    """Call Azure ML endpoint"""
    url = os.getenv('MLFLOW_ENDPOINT')
    headers = {'Authorization': f'Bearer {os.getenv("MLFLOW_API_KEY")}'}
    response = requests.post(url, json=input_data, headers=headers)
    return response.json()
```

---

## Performance Tips

- Load historical data once per session
- Cache expensive computations with `@st.cache_data`
- Use pagination for large datasets
- Optimize queries for real data

---

## Support

For questions or issues:
1. Check `README.md` in `src/ui/`
2. Review mock data generation in `mock_data.py`
3. Check Streamlit documentation: https://docs.streamlit.io

---

**Created:** November 14, 2025  
**Status:** ✅ Ready to Use  
**Dashboard Version:** 1.0

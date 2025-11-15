# SmartArchive ML POC - Streamlit UI Setup

To run the Streamlit dashboard:

```bash
# Install Streamlit (if not already installed)
pip install streamlit plotly

# Run the app
cd ml-poc
streamlit run src/ui/streamlit_app.py
```

The dashboard will open at: `http://localhost:8501`

## Features

- **Summary Metrics**: Current archive size, predictions, savings, and model accuracy
- **Historical vs Predicted**: Time series chart showing historical data and forecasts with confidence intervals
- **File Type Distribution**: Pie chart showing breakdown by file type
- **Savings Projection**: Bar chart and cumulative savings over time
- **Scenario Simulator**: Interactive sliders to test different archive strategies
- **Model Performance**: Accuracy metrics and model information
- **Data Export**: Download predictions as CSV

## Mock Data

Currently uses mock/synthetic data for demonstration. 

To connect real data:
1. Update `mock_data.py` to query your actual archive database
2. Or replace mock data functions with real data endpoints

## File Structure

```
src/ui/
├── __init__.py              # Package marker
├── streamlit_app.py         # Main Streamlit app
├── mock_data.py             # Mock data generation
└── README.md                # This file
```

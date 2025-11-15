# GitHub Copilot Instructions for SmartArchive ML-POC

This document contains specific instructions and patterns for GitHub Copilot to follow when working on the SmartArchive ML-POC project. These guidelines help ensure consistency, maintainability, and alignment with the project architecture.

## Project Overview

**SmartArchive ML-POC** is a machine learning proof-of-concept system that:
- Uses Azure ML Studio to host a RandomForest ML model (R²=0.875)
- Provides a Streamlit web dashboard for forecasting SharePoint archive storage
- Implements monitoring with drift detection and prediction tracking
- Stores data locally using SQLite for POC phase

**Key Technologies:**
- Python 3.10+ (Anaconda ml-env)
- Streamlit 1.31.1 (dashboard UI)
- Azure ML Studio (model deployment, SouthEast Asia)
- SQLite (local monitoring DB)
- pandas, numpy, scikit-learn (ML stack)
- scipy.stats (statistical tests)

## Architecture Patterns

### Project Structure

```
ml-poc/
├── src/
│   ├── ui/
│   │   ├── streamlit_app.py        # Main dashboard (8 sections)
│   │   ├── mock_data.py            # Synthetic data generation (9 features)
│   │   ├── monitoring_dashboard.py # Monitoring dashboard component (Phase 2)
│   │   └── __init__.py
│   ├── ml/
│   │   ├── azure_endpoint_client.py # Azure ML bridge (complete)
│   │   └── azure_ml_pipeline.py
│   ├── monitoring/
│   │   ├── predictions_db.py        # SQLite storage layer
│   │   ├── drift_detector.py        # Statistical drift detection
│   │   ├── alerts.py               # Alert management (Phase 2)
│   │   └── __init__.py
│   ├── scripts/
│   │   ├── generate_sample_data.py  # Generate test data for monitoring
│   │   └── __init__.py
│   └── tests/
│       └── test_monitoring_integration.py  # Phase 1 integration tests (8 tests)
├── docs/
│   ├── architecture.md             # System design with Mermaid diagrams
│   ├── monitoring-design.md        # Monitoring system specification
│   └── logids.md
├── config/
├── test_data/
└── requirements.txt                # Python dependencies
```

### Azure ML Integration Pattern

**Model Input:** 9 features
- `total_files`: Total files in site
- `avg_file_size_mb`: Average file size
- `pct_pdf`, `pct_docx`, `pct_xlsx`, `pct_other`: File type percentages
- `archive_frequency_per_day`: Archive rate
- `month_sin`, `month_cos`: Cyclical month encoding

**Model Output:** 2 predictions
- `archived_gb`: Forecasted archived storage (GB)
- `savings_gb`: Forecasted storage savings (GB)

**Azure ML Endpoint:**
- URL: `https://mlflow-workspace-qzgku.southeastasia.inference.ml.azure.com/score`
- Method: POST with JSON payload
- Request format: `{"input_data": {"columns": [...], "index": [...], "data": [...]}}`
- Response format: `[[archived_gb, savings_gb], [...]]`
- Error handling: 401 (auth), 404 (not found), 424 (format), 5xx (fallback to mock)

### Data Flow

1. **Streamlit Dashboard** calls `AzureMLEndpointClient.call_endpoint()`
2. **Azure ML Endpoint** receives 9 features, returns 2 predictions
3. **Predictions stored** in SQLite via `PredictionsDB.save_prediction()`
4. **Drift detection** runs via `DriftDetector.check_all_drifts()`
5. **Events logged** to monitoring_events table
6. **Dashboard displays** real predictions with success indicator

## Code Style & Patterns

### Python Code Standards

**Naming Conventions:**
- Classes: `PascalCase` (e.g., `DriftDetector`, `AzureMLEndpointClient`)
- Functions: `snake_case` (e.g., `save_prediction()`, `detect_anomalies_zscore()`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `Z_SCORE_THRESHOLD = 2.0`)
- Private methods: `_leading_underscore` (e.g., `_initialize_db()`)

**Async/Await Pattern:**
- All HTTP calls use `requests` library (not async)
- Database operations are synchronous with SQLite context manager pattern

```python
# ✅ CORRECT - Context manager pattern for database
with PredictionsDB() as db:
    db.save_prediction(...)
    predictions = db.get_predictions()
```

**Documentation:**
- Module docstring at top of every `.py` file
- Class docstrings with purpose and usage
- Method docstrings with Args, Returns, and examples
- Inline comments only for non-obvious logic

```python
"""
Module Purpose

Handles specific domain functionality.
Usage: 
    from src.module import ClassName
    obj = ClassName()
    result = obj.method()
"""

class MyClass:
    """Purpose of class with one-line summary
    
    Longer description explaining key behavior.
    """
    
    def my_method(self, param1: str, param2: int = 10) -> Dict:
        """Method summary
        
        Args:
            param1: Description of param1
            param2: Description of param2 (default: 10)
        
        Returns:
            Dictionary with keys:
            - 'result': The main result
            - 'status': Operation status ('success' or 'error')
        """
```

### Error Handling Pattern

**Exception Handling:**
- Catch specific exceptions, not bare `except`
- Log errors before returning or re-raising
- Return error dictionaries with 'error' key for non-critical failures

```python
# ✅ CORRECT - Specific exception handling with logging
try:
    result = endpoint.call()
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    return {'error': 'Connection failed', 'details': str(e)}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# ❌ WRONG - Bare except or generic Exception
try:
    result = endpoint.call()
except:  # Don't do this
    pass
```

### Type Hints

Always use type hints for function signatures:

```python
# ✅ CORRECT - Type hints throughout
def save_prediction(
    self,
    prediction_date: str,
    archived_gb_predicted: float,
    savings_gb_predicted: float,
    archived_gb_actual: Optional[float] = None
) -> int:
    """Save prediction and return ID"""
```

### Return Values from Functions

- Functions return actual values on success (not tuples with status)
- Return `None` for "not found" scenarios (not False or error codes)
- Return dictionaries with consistent keys for complex results

```python
# ✅ CORRECT - Clear return patterns
def get_latest_prediction(self) -> Optional[Dict]:
    """Returns dict or None"""
    
def get_predictions(self, days: int) -> pd.DataFrame:
    """Always returns DataFrame (empty if no data)"""

def detect_anomalies_zscore(self, values) -> Dict:
    """Always returns dict with consistent structure"""
    return {
        'has_anomalies': bool,
        'anomaly_count': int,
        'anomaly_indices': List[int],
        # ... more keys
    }
```

## Module-Specific Patterns

### 1. Azure ML Client (`src/ml/azure_endpoint_client.py`)

**Purpose:** Bridge between Streamlit dashboard and Azure ML endpoint

**Key Classes:**
- `AzureMLEndpointClient`: Main client for endpoint communication

**Key Methods:**
- `__init__(api_key, endpoint_url)`: Initialize with credentials
- `prepare_request_payload(df)`: Convert 9-feature DataFrame to endpoint format
- `call_endpoint(df)`: Send request, return predictions or mock data
- `get_predictions()`: Public API for getting forecasts
- `get_model_metrics()`: Return model performance metadata

**Usage Pattern:**
```python
from src.ml.azure_endpoint_client import AzureMLEndpointClient

client = AzureMLEndpointClient(
    api_key=os.getenv('AZURE_ML_API_KEY'),
    endpoint_url=os.getenv('AZURE_ML_ENDPOINT_URL')
)

# Prepare 9-feature DataFrame
df = prepare_feature_dataframe(...)

# Get predictions (auto fallback to mock)
predictions = client.get_predictions(df)
metrics = client.get_model_metrics()
```

**Error Handling:**
- Returns mock data on any Azure ML error
- Logs error but doesn't crash dashboard
- Always returns valid predictions DataFrame

### 2. Predictions Database (`src/monitoring/predictions_db.py`)

**Purpose:** SQLite wrapper for storing predictions and events

**Key Classes:**
- `PredictionsDB`: Database operations wrapper

**Schema:**
- `predictions`: prediction_date, archived_gb_predicted, savings_gb_predicted, archived_gb_actual, savings_gb_actual, created_at
- `monitoring_events`: event_type, event_severity, message, metadata, created_at
- `model_metrics`: metric_date, r2_score, rmse, mae, mape, accuracy, created_at

**Key Methods:**
- `__init__(db_path)`: Initialize database
- `save_prediction(...)`: Store forecast
- `update_actual_value(...)`: Update with actual values later
- `get_predictions(days=30)`: Retrieve recent predictions
- `get_recent_predictions_for_drift(window_size=30)`: For drift detection
- `save_monitoring_event(...)`: Log events
- `get_summary_statistics(days=30)`: Get overview

**Usage Pattern:**
```python
from src.monitoring import PredictionsDB

# With context manager
with PredictionsDB('predictions.db') as db:
    db.save_prediction('2025-01-01', 250.5, 130.2)
    predictions = db.get_predictions(days=30)
    stats = db.get_summary_statistics()

# Or without context manager
db = PredictionsDB()
try:
    db.save_prediction(...)
finally:
    db.close()
```

**Important:**
- Always use context manager when possible
- Database is local SQLite (no async needed)
- All queries return DataFrames or None/empty
- Timestamps are CURRENT_TIMESTAMP (UTC)

### 3. Drift Detector (`src/monitoring/drift_detector.py`)

**Purpose:** Statistical drift detection using multiple methods

**Key Classes:**
- `DriftDetector`: Statistical methods for drift detection

**Detection Methods:**

1. **Z-Score Anomaly Detection:**
   - Flags values with |z-score| > threshold (default: 2.0)
   - Uses baseline mean/std if set, otherwise calculates from data
   - Best for: Detecting outliers in predictions

2. **KS Test Distribution Drift:**
   - Compares current distribution to baseline
   - Returns p-value: low p-value = distributions different
   - Best for: Detecting overall distribution shift

3. **Trend Drift Detection:**
   - Compares recent vs older means
   - Calculates simple linear trend (slope)
   - Best for: Detecting gradual model degradation

**Key Methods:**
- `set_baseline(values)`: Establish baseline for comparison
- `detect_anomalies_zscore(values)`: Find outliers
- `detect_drift_ks_test(current_values)`: Test distribution shift
- `detect_trend_drift(values)`: Analyze trend over time
- `check_all_drifts(values)`: Run all methods, return summary
- `get_drift_summary(results)`: Human-readable string

**Usage Pattern:**
```python
from src.monitoring import DriftDetector

detector = DriftDetector(
    z_score_threshold=2.0,      # ~95% confidence
    ks_test_threshold=0.05,      # 5% significance level
    min_samples=10
)

# Set baseline from initial data
baseline_predictions = [250, 252, 248, 251, 249, ...]
detector.set_baseline(baseline_predictions)

# Check current predictions for drift
current_predictions = [250, 252, 248, 251, 249, ...]
results = detector.check_all_drifts(current_predictions)
print(detector.get_drift_summary(results))
```

**Result Structure:**
```python
{
    'overall_drift_detected': bool,
    'anomalies': {
        'has_anomalies': bool,
        'anomaly_count': int,
        'z_scores': List[float],
        'max_z_score': float,
        ...
    },
    'distribution_drift': {
        'has_drift': bool,
        'ks_statistic': float,
        'p_value': float,
        'mean_change_pct': float,
        ...
    },
    'trend_drift': {
        'has_trend_drift': bool,
        'trend_direction': str,  # 'up', 'down', 'stable'
        'trend_change_pct': float,
        'slope': float,
        ...
    }
}
```

### 4. Streamlit Dashboard (`src/ui/streamlit_app.py`)

**Purpose:** Web UI for forecasting and monitoring

**Architecture:**
- 8 main sections (sidebar + pages)
- Azure ML predictions with mock data fallback
- Interactive charts using Plotly
- Simulator for what-if analysis

**Key Sections:**
1. **Summary Metrics**: KPIs and current forecast
2. **Predictions Chart**: Historical and forecasted values
3. **Confidence Intervals**: Optional (when available)
4. **Simulator**: What-if analysis tool
5. **Export Data**: Download forecasts as CSV
6. **Model Performance**: Metrics and accuracy
7. **Monitoring** (Phase 2): Drift detection and events
8. **Settings**: Configuration options

**Azure ML Integration:**
- Line 51-60: Import with try-catch for graceful fallback
- Line 405-420: Prediction loading (Azure first, mock fallback)
- Line 133-171: Safe metric retrieval with `.get(key, default)`
- Line 350-371: Model performance with fallback values

**Important Patterns:**
- All `.get()` calls have defaults for optional metrics
- Check for column existence before using (some versions may differ)
- Use `st.success()`, `st.warning()`, `st.error()` for feedback
- Cache expensive operations with `@st.cache_data`

```python
# ✅ CORRECT - Safe metric access
metrics = predictions.get('metrics', {})
r2_score = metrics.get('r2_score', 0.0)
rmse = metrics.get('rmse', 0.0)

# ❌ WRONG - Will crash if keys missing
metrics = predictions['metrics']
r2_score = metrics['r2_score']
```

### 5. Mock Data (`src/ui/mock_data.py`)

**Purpose:** Generate synthetic data for development and testing

**Key Functions:**
- `get_mock_historical_data(days=30)`: Generate 9-feature DataFrame
- `get_mock_metrics()`: Return fake model metrics

**9 Required Features:**
1. `total_files`: Random integer (100-5000)
2. `avg_file_size_mb`: Random float (1.0-50.0)
3. `pct_pdf`: Percentage (0-100)
4. `pct_docx`: Percentage (0-100)
5. `pct_xlsx`: Percentage (0-100)
6. `pct_other`: Percentage (0-100) - should sum to 100
7. `archive_frequency_per_day`: Random float (0.1-10.0)
8. `month_sin`: sin(month * 2π/12)
9. `month_cos`: cos(month * 2π/12)

**Important:**
- File type percentages must sum to ~100%
- Dates should span specified range
- Values should be realistic ranges
- Used for testing AND as fallback when Azure ML unavailable

### 6. Sample Data Generator (`src/scripts/generate_sample_data.py`)

**Purpose:** Generate realistic monitoring data for dashboard testing

**Key Function:**
- `generate_sample_data(days=30, db_path='monitoring.db')`: Create 30 days of predictions with drift and alerts

**What It Generates:**
- **Baseline predictions** (first half): Normal distribution (mean=250 GB, std=15)
- **Recent predictions** (second half): Upward trend (+1.5 GB/day) 
- **Anomalies**: Random outliers every 5th day (±50/-40 GB)
- **Drift detection**: Runs detector and creates alerts if drift found
- **Monitoring events**: Sample log entries for model predictions and drift checks
- **Database**: Populates predictions, monitoring_events, and creates alerts

**Usage:**
```bash
cd ml-poc
python src/scripts/generate_sample_data.py
```

**Output:**
- Updates `monitoring.db` with 30 days of data
- Creates sample alerts if drift detected
- Prints summary statistics and instructions
- Message: "Run streamlit run src/ui/streamlit_app.py to view data"

**Important:**
- Run from ml-poc root directory (uses relative path to monitoring.db)
- Creates database if it doesn't exist
- Gracefully closes database connection via try-finally
- Safe to run multiple times (appends new data)

## Common Development Tasks

### Adding a New Feature to Dashboard

1. Create new Streamlit page/section in `streamlit_app.py`
2. Generate mock data if needed in `mock_data.py`
3. Update Azure ML client if new predictions needed
4. Add to monitoring if tracking required
5. Test with both Azure ML and mock data

### Adding Monitoring Capability

1. Create DriftDetector instance with appropriate thresholds
2. Call `check_all_drifts()` with recent predictions
3. Log events via `db.save_monitoring_event()` if drift detected
4. Display alerts in dashboard (Phase 2)

### Testing New Code

**Pattern for testing:**
- Add `if __name__ == "__main__":` section with tests
- Use print() for output (don't import pytest for POC)
- Test with sample data
- Include both success and failure scenarios
- Example: See bottom of `drift_detector.py`

**Important:**
- Don't run Python scripts via terminal command prompts
- All testing is embedded in modules via `__main__` blocks
- Use `python module.py` pattern for module-level testing

## Common Mistakes to Avoid

### 1. Azure ML Integration Mistakes
- ❌ Forgetting to handle connection errors gracefully
- ❌ Assuming metrics keys exist without checking
- ❌ Not converting DataFrame to endpoint input format
- ❌ Using wrong API key or endpoint URL

**Fix:**
```python
try:
    predictions = client.call_endpoint(df)
except Exception as e:
    logger.error(f"Azure ML failed: {e}")
    predictions = get_mock_data()  # Fallback
```

### 2. Monitoring Database Mistakes
- ❌ Not using context manager (may leave connections open)
- ❌ Assuming prediction exists without checking
- ❌ Not handling database locked errors
- ❌ Forgetting `immediately=True` in save operations (not applicable here)

**Fix:**
```python
with PredictionsDB() as db:
    db.save_prediction(...)
    latest = db.get_latest_prediction()
    if latest is None:
        logger.warning("No predictions found")
```

### 3. Drift Detection Mistakes
- ❌ Not setting baseline before detection
- ❌ Using too few samples (< min_samples threshold)
- ❌ Ignoring error keys in result dictionary
- ❌ Not checking 'overall_drift_detected' flag

**Fix:**
```python
detector = DriftDetector(min_samples=10)
if len(values) < 10:
    return  # Skip drift check

detector.set_baseline(baseline_values)
results = detector.check_all_drifts(current_values)
if results['overall_drift_detected']:
    # Take action
```

### 4. Streamlit Display Mistakes
- ❌ Not checking column existence before display
- ❌ Not providing defaults for optional values
- ❌ Using `st.write(df)` without column selection
- ❌ Not clearing session state when needed

**Fix:**
```python
# Always check before accessing
if 'confidence_upper' in predictions.columns:
    st.line_chart(predictions['confidence_upper'])

# Always provide defaults
value = metrics.get('r2_score', 0.0)
st.metric('R² Score', f"{value:.3f}")
```

### 5. Data Type Mistakes
- ❌ Mixing DataFrame and list operations
- ❌ Not converting strings to datetime
- ❌ Forgetting to convert percentages (0-100 vs 0-1)
- ❌ Not handling None/NaN values

**Fix:**
```python
# Always convert dates
df['prediction_date'] = pd.to_datetime(df['prediction_date'])

# Check for None
if value is not None:
    processed = value / 100  # If percentage

# Handle NaN
df.fillna(0, inplace=True)
```

## Testing Patterns

### Module-Level Testing

All modules include a `if __name__ == "__main__":` test section:

```python
if __name__ == "__main__":
    print("Testing ModuleName...")
    print("=" * 60)
    
    # Test 1
    print("\n✓ Test 1: Feature description")
    # ... test code ...
    
    # Test 2
    print("\n✓ Test 2: Feature description")
    # ... test code ...
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
```

**Running Tests:**
- Each module can be run directly: `python src/monitoring/drift_detector.py`
- Integration test available: `python test_monitoring_integration.py`
- No external test framework for POC phase

## Environment Setup

### Required Environment Variables

Create `.env` file in project root:

```env
AZURE_ML_API_KEY=your_api_key_here
AZURE_ML_ENDPOINT_URL=https://mlflow-workspace-qzgku.southeastasia.inference.ml.azure.com/score
STREAMLIT_LOGGING_LEVEL=info
```

### Python Dependencies

Install from `requirements.txt`:
```bash
pip install -r requirements.txt
```

**Key Packages:**
- streamlit==1.31.1
- pandas>=2.0.0
- numpy>=1.24.0
- scikit-learn>=1.3.0
- scipy>=1.11.0
- plotly>=5.18.0
- requests>=2.31.0
- python-dotenv>=1.0.0

## Documentation Standards

### Markdown Files - General

Use lowercase filenames with hyphens for general documentation:
- ✅ `architecture.md`
- ✅ `monitoring-design.md`
- ✅ `copilot-instructions.md`
- ❌ `ARCHITECTURE.MD`
- ❌ `Architecture_Doc.md`

### Status Updates & Assessment Files

Status updates and assessment files must follow specific patterns:

**Location:** `docs/assessment/status_updates/`

**File Naming Convention:**
- Format: `YYYY-MM-DD-PascalCaseName.md`
- ✅ `2025-11-14-Monitoring-Plan.md`
- ✅ `2025-11-14-Assessment-Update.md`
- ✅ `2025-11-14-Progress-Report.md`
- ❌ `2025-11-14-MONITORING_PLAN.md` (ALL CAPS)
- ❌ `2025-11-14-monitoring-plan.md` (lowercase)
- ❌ `20251114-Assessment.md` (wrong date format)

**Assessment Files Location:** `docs/assessment/`

**Assessment File Naming:**
- Format: `ASSESSMENT_Descriptor.md` (PascalCase after underscore)
- ✅ `ASSESSMENT_Quick.md`
- ✅ `ASSESSMENT_Details.md`
- ✅ `ASSESSMENT_Update.md`
- ❌ `assessment_quick.md` (wrong case)
- ❌ `ASSESSMENT_quick.md` (inconsistent case)

**When Creating Status Updates:**
1. Always store in `docs/assessment/status_updates/`
2. Always use `YYYY-MM-DD` prefix (today's date)
3. Use PascalCase for the descriptive part (capitalize each word, no hyphens after date)
4. Follow existing files for consistency (see 2025-11-14-OUTPERFORM_MONITORING_PLAN.md pattern)

### Comment Style

```python
# ✅ CORRECT - Clear, concise comments
# Calculate z-scores for anomaly detection (threshold: 2.0 = 95% confidence)
z_scores = np.abs((np.array(values) - mean) / std)

# ❌ WRONG - Unclear or obvious comments
# Loop through values
for value in values:
    # Add value
    total += value
```

### Docstring Style

```python
# ✅ CORRECT - Full docstring
def get_predictions(self, days: int = 30) -> pd.DataFrame:
    """
    Get predictions from the last N days
    
    Args:
        days: Number of days to retrieve (default: 30)
    
    Returns:
        DataFrame with columns: prediction_date, archived_gb_predicted, 
        savings_gb_predicted, archived_gb_actual, savings_gb_actual, created_at
        Returns empty DataFrame if no data found.
    
    Example:
        predictions = db.get_predictions(days=7)
        print(f"Got {len(predictions)} predictions")
    """
```

## Performance Guidelines

### Streamlit Caching

Use `@st.cache_data` for expensive operations:

```python
@st.cache_data
def get_predictions_cached(days: int):
    """This is called once per day parameter, not on every rerun"""
    return db.get_predictions(days=days)
```

### Database Query Performance

- Always specify `days` filter to limit query scope
- Use `LIMIT` for large result sets
- Create indexes on frequently queried columns in Phase 2
- For POC: SQLite is sufficient (typical ~1000 rows/month)

### Chart Performance

- Limit plotly chart to 1000 points max
- Use sampling for large datasets
- Cache chart generation for interactive elements

## Version Control Guidelines

### Commit Messages

```
# ✅ CORRECT - Clear, descriptive
feat: Add drift detection to monitoring system
fix: Handle missing Azure ML metrics gracefully
docs: Update architecture documentation with monitoring design

# ❌ WRONG - Unclear
updated stuff
fixed bugs
wip
```

### Pull Request Process

1. Feature branch from `ml-poc`
2. Include tests in module (via `__main__` block)
3. Update relevant `.md` files
4. Request review before merging

## Summary

**Key Principles:**
1. **Graceful Degradation:** Always fallback to mock data
2. **Type Safety:** Always use type hints
3. **Clear Documentation:** Every module has docstrings
4. **Error Handling:** Catch specific exceptions, log errors
5. **Testing:** Embed tests in modules via `__main__`
6. **Consistency:** Follow established patterns in similar code
7. **No Async Complexity:** Keep everything synchronous for POC
8. **Local First:** Use SQLite, not cloud services for monitoring

**When in Doubt:**
- Look at existing similar implementations in the codebase
- Check module docstrings and examples
- Review the architecture diagram in `docs/architecture.md`
- Run module tests: `python src/monitoring/module_name.py`

---

**Last Updated:** November 14, 2025  
**Status:** 🟩 EXCELLENT (92/100) - Azure ML integrated, monitoring system in progress

# 🎯 Outperform Priority #1: Monitoring & Drift Detection Plan

**Status:** 🟩 Ready to Start  
**Timeline:** 1 week (5 working days)  
**Effort:** Medium (40-50 hours)  
**Blocker:** ❌ None - can start immediately  
**Blockers for later:** ✅ Real data needed for items 4-5

---

## 📋 Deliverables

By end of this work, you'll have:

1. ✅ **New "Monitoring" Tab in Streamlit Dashboard**
   - Performance metrics over time
   - Data drift detection results
   - Prediction drift visualization
   - Alert indicators

2. ✅ **Drift Detection System**
   - Data drift detector (statistical tests)
   - Prediction drift detector (accuracy degradation)
   - Alerting logic (thresholds)

3. ✅ **Metrics Logging System**
   - Predictions logged to CSV/database
   - Metrics calculated on schedule
   - Historical tracking

4. ✅ **Monitoring Report Generator**
   - Daily/weekly summary reports
   - Alert summaries
   - Trend analysis

5. ✅ **Documentation**
   - How to interpret drift alerts
   - Troubleshooting guide
   - Configuration options

---

## 🏗️ Architecture Overview

```
Streamlit App (src/ui/)
├── streamlit_app.py (existing + monitoring tab)
├── monitoring.py (NEW)
│   ├── drift_detector.py (NEW)
│   ├── metrics_logger.py (NEW)
│   └── alert_system.py (NEW)
└── mock_data.py (existing + logging)

Data Storage
├── logs/monitoring/ (NEW)
│   ├── predictions.csv (NEW - daily)
│   ├── metrics.csv (NEW - daily)
│   └── alerts.csv (NEW - as needed)
└── reports/ (NEW)
    ├── daily_report_2025-11-14.txt (NEW)
    └── weekly_report_2025-11-14.txt (NEW)
```

---

## 📊 Monitoring Dashboard Tab Design

### Part 1: Real-Time Metrics (Top Section)
```
┌─────────────────────────────────────────────────┐
│ 📊 MONITORING DASHBOARD                          │
├─────────────────────────────────────────────────┤
│ Last Updated: 2025-11-14 15:30 UTC              │
├─────────────────────────────────────────────────┤
│ ┌──────────────┬──────────────┬──────────────┐  │
│ │ Predictions  │ Drift Status │ Alert Count  │  │
│ │  Made Today  │   ✅ NORMAL  │   0 Active   │  │
│ │     1,247    │              │              │  │
│ └──────────────┴──────────────┴──────────────┘  │
│ ┌──────────────┬──────────────┬──────────────┐  │
│ │  Avg Pred    │  Model Age   │ Last Retrain │  │
│ │   574.2 GB   │   14 days    │   Nov 1 ✅  │  │
│ └──────────────┴──────────────┴──────────────┘  │
└─────────────────────────────────────────────────┘
```

### Part 2: Performance Trends (Middle Section)
```
┌─────────────────────────────────────────────────┐
│ 📈 PERFORMANCE TRACKING (Last 30 days)           │
├─────────────────────────────────────────────────┤
│ Model Accuracy (R²) Over Time                    │
│ 0.90 ┬─────────────┐                            │
│ 0.80 │ ╱╲    ╱╲    │  Target: >0.75            │
│ 0.70 │╱  ╲  ╱  ╲   │  Current: 0.875 ✅       │
│ 0.60 └────────────┘ Average: 0.85               │
│   Nov1       Nov14                              │
└─────────────────────────────────────────────────┘
```

### Part 3: Drift Detection (Bottom Section)
```
┌─────────────────────────────────────────────────┐
│ ⚠️ DRIFT DETECTION ANALYSIS                      │
├─────────────────────────────────────────────────┤
│ Data Drift: ✅ NORMAL (Kolmogorov-Smirnov)      │
│   Archive_GB distribution: 98.5% similar        │
│   Total Files: 97.2% similar                    │
│   Avg File Size: 96.8% similar                  │
│                                                  │
│ Prediction Drift: ✅ NORMAL                      │
│   Accuracy degradation: -0.8% (within threshold)│
│   Prediction variance: Normal                   │
│   Outlier predictions: 2 (0.16% - OK)          │
│                                                  │
│ 🟢 STATUS: Model performing well                │
│ ✅ No retraining needed (check again in 7 days) │
└─────────────────────────────────────────────────┘
```

### Part 4: Alerts & Incidents (If any)
```
┌─────────────────────────────────────────────────┐
│ 🚨 ACTIVE ALERTS (Last 30 days)                  │
├─────────────────────────────────────────────────┤
│ No active alerts ✅                              │
│                                                  │
│ Historical Alerts:                              │
│ • Nov 10: High variance in predictions (+2% OK) │
│ • Nov 5: Data spike detected (handled OK)       │
│ • Oct 28: Accuracy dipped to 0.72 (recovered)  │
└─────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Tasks (Day by Day)

### Day 1: Setup & Data Logging (4 hours)
**Goal:** Create logging infrastructure

- [ ] Create `src/ui/monitoring.py` main module
- [ ] Create `src/ui/drift_detector.py` class
- [ ] Create `logs/monitoring/` directory structure
- [ ] Create `_create_prediction_logger()` function
  - Logs each prediction to CSV
  - Includes timestamp, input, output, model version
- [ ] Update `streamlit_app.py` to call logger on each prediction
- [ ] Test: Verify logs are created and contain correct data

**Files to create:**
```
src/ui/
├── monitoring.py (50 lines)
└── drift_detector.py (100 lines)

logs/monitoring/
├── predictions.csv (NEW, auto-created)
├── metrics.csv (NEW, auto-created)
└── alerts.csv (NEW, auto-created)
```

### Day 2: Drift Detection Logic (6 hours)
**Goal:** Implement drift detection algorithms

- [ ] Implement `detect_data_drift()` function
  - Kolmogorov-Smirnov test (univariate drift)
  - Kullback-Leibler divergence (multivariate)
  - Compare: current 30 days vs. baseline (first 30 days)
  - Return: drift_score (0-1), verdict (Normal/Warning/Critical)

- [ ] Implement `detect_prediction_drift()` function
  - Track prediction accuracy over rolling windows
  - Calculate trend (improving/degrading/stable)
  - Detect outlier predictions (>3σ)
  - Return: drift_score, verdict, reason

- [ ] Create `AlertSystem` class
  - Define thresholds (Warning: >0.2, Critical: >0.5)
  - Create alert records
  - Log to alerts.csv

**Files to update:**
```
src/ui/drift_detector.py (add 200 lines)
  • DriftDetector class
  • detect_data_drift()
  • detect_prediction_drift()
  • _kolmogorov_smirnov_test()
  • _calculate_kullback_leibler()
```

### Day 3: Metrics Calculation (4 hours)
**Goal:** Calculate and track monitoring metrics

- [ ] Create `MetricsCalculator` class
  - Calculate daily metrics from logs
  - Accuracy metrics (MAE, RMSE, R²)
  - Data metrics (mean, std, quantiles)
  - Prediction metrics (variance, outlier %)
  - Store in metrics.csv

- [ ] Create `_load_predictions_for_period()` helper
  - Load last N days/weeks from CSV
  - Handle missing dates gracefully

- [ ] Implement metric aggregation
  - Daily summaries
  - Weekly summaries
  - 30-day rolling window

**Files to create:**
```
src/ui/metrics_logger.py (150 lines)
  • MetricsCalculator class
  • calculate_daily_metrics()
  • calculate_rolling_metrics()
```

### Day 4: Streamlit Monitoring Tab (5 hours)
**Goal:** Create beautiful monitoring dashboard

- [ ] Add "Monitoring" tab to `streamlit_app.py`
  - Use `st.tabs()` to add new tab
  - Add session state for caching

- [ ] Implement real-time metrics section
  - Read latest from metrics.csv
  - Display in nice cards with color coding
  - Add refresh button

- [ ] Implement performance trends chart
  - Plot R² over 30 days
  - Add confidence band
  - Show warning/critical thresholds

- [ ] Implement drift detection section
  - Display data drift results
  - Display prediction drift results
  - Show last assessment time
  - Add "Run drift check now" button

- [ ] Implement alerts section
  - List active alerts (red background)
  - List recent resolved alerts (yellow)
  - List clear status (green)
  - Show alert trend chart

**Files to update:**
```
src/ui/streamlit_app.py (add 300-400 lines)
  • create_monitoring_section()
  • display_realtime_metrics()
  • display_performance_trends()
  • display_drift_analysis()
  • display_alerts()
  • load_logs_data() helper
```

### Day 5: Testing & Documentation (5 hours)
**Goal:** Finalize, test, and document

- [ ] Integration testing
  - Run streamlit app
  - Verify monitoring tab loads
  - Make predictions and check logs
  - Run drift detection manually
  - Check charts render correctly

- [ ] Create monitoring runbook
  - How to interpret each metric
  - What drift detection means
  - What to do when alerts fire
  - How to manually trigger retraining

- [ ] Create configuration guide
  - How to adjust drift thresholds
  - How to change alert levels
  - How to add new metrics

- [ ] Documentation in code
  - Add docstrings to all functions
  - Add comments for complex logic
  - Add type hints everywhere

**Files to create:**
```
MONITORING_GUIDE.md (300 lines)
  • Overview
  • How to interpret metrics
  • Drift detection explanation
  • Alert response guide
  • Troubleshooting
  • Configuration reference

src/ui/monitoring.py (add docstrings)
src/ui/drift_detector.py (add docstrings)
src/ui/metrics_logger.py (add docstrings)
```

---

## 💻 Code Skeleton

### src/ui/drift_detector.py
```python
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
from dataclasses import dataclass

@dataclass
class DriftResult:
    drift_score: float  # 0-1
    verdict: str  # "Normal" | "Warning" | "Critical"
    details: dict  # What changed
    timestamp: str

class DriftDetector:
    def __init__(self, baseline_df: pd.DataFrame, threshold_warning=0.2, threshold_critical=0.5):
        self.baseline = baseline_df
        self.threshold_warning = threshold_warning
        self.threshold_critical = threshold_critical
    
    def detect_data_drift(self, current_df: pd.DataFrame) -> DriftResult:
        """Detect data drift using statistical tests"""
        # KS test for each column
        # Average the drift scores
        # Return DriftResult
        pass
    
    def detect_prediction_drift(self, predictions_df: pd.DataFrame) -> DriftResult:
        """Detect if model predictions are drifting"""
        # Calculate accuracy trends
        # Check for outliers
        # Return DriftResult
        pass

class AlertSystem:
    def __init__(self):
        self.active_alerts = []
        self.alert_history = []
    
    def raise_alert(self, alert_type: str, severity: str, message: str):
        """Create and log an alert"""
        pass
    
    def resolve_alert(self, alert_id: str):
        """Mark alert as resolved"""
        pass
```

### src/ui/metrics_logger.py
```python
import pandas as pd
from pathlib import Path
from datetime import datetime

class MetricsCalculator:
    def __init__(self, logs_dir: Path = Path("logs/monitoring")):
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def log_prediction(self, input_data: dict, prediction: float, model_version: str):
        """Log a single prediction"""
        # Add to predictions.csv
        pass
    
    def calculate_daily_metrics(self, date: str = None) -> dict:
        """Calculate metrics for a given day"""
        # Load predictions for that day
        # Calculate MAE, RMSE, R²
        # Return metrics dict
        pass
    
    def get_rolling_metrics(self, days: int = 30) -> pd.DataFrame:
        """Get rolling metrics over N days"""
        # Load all predictions for last N days
        # Calculate daily metrics for each
        # Return DataFrame with date and metrics
        pass
```

### src/ui/streamlit_app.py (add to existing)
```python
def create_monitoring_section():
    """Create the monitoring dashboard tab"""
    with st.expander("📊 Monitoring & Drift Detection", expanded=False):
        
        # Load data
        predictions_df = load_predictions_csv()
        metrics_df = load_metrics_csv()
        alerts_df = load_alerts_csv()
        
        # Real-time metrics (top)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Predictions Today", len(predictions_df))
        with col2:
            drift_status = detect_data_drift(predictions_df)
            st.metric("Drift Status", drift_status.verdict, delta=f"{drift_status.drift_score:.1%}")
        with col3:
            st.metric("Active Alerts", len([a for a in alerts_df if a['status'] == 'active']))
        
        # Performance trends chart
        st.subheader("📈 Performance Trends (30 days)")
        fig = create_performance_chart(metrics_df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Drift analysis
        st.subheader("⚠️ Drift Detection Analysis")
        data_drift = detect_data_drift(predictions_df)
        pred_drift = detect_prediction_drift(metrics_df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Data Drift:** {data_drift.verdict}")
            st.write(f"Score: {data_drift.drift_score:.1%}")
        with col2:
            st.write(f"**Prediction Drift:** {pred_drift.verdict}")
            st.write(f"Score: {pred_drift.drift_score:.1%}")
        
        # Alerts
        st.subheader("🚨 Alerts")
        if len(alerts_df) > 0:
            st.dataframe(alerts_df)
        else:
            st.success("✅ No active alerts")
```

---

## 📈 Success Criteria

By end of this work:

- ✅ Monitoring tab appears in Streamlit app
- ✅ Predictions are logged to CSV on each run
- ✅ Drift detection runs on demand
- ✅ Metrics calculated daily
- ✅ Alerts fire when thresholds exceeded
- ✅ All 4 charts render without errors
- ✅ Documentation complete
- ✅ Tested with mock data for 48 hours

---

## 📊 Expected Outcome

After this work:
- 🟨 Status: **Successful** → 🟩 **Excellent** (complete)
- 🟩 Status: **Excellent** → 🟢 **Outperform** (partially - monitoring added ✅)

**Remaining for full Outperform:**
- Real data integration (needs data)
- Cloud deployment (needs data)
- Automated retraining (needs data + monitoring)
- CI/CD pipeline (independent, 1 week)

---

## 🚀 Start Date

**Ready to start:** Now!  
**Estimated completion:** November 21, 2025  
**Blocker for next phases:** Real archive data needed

Ready to begin? Let me know and I'll help you set up the first day's work! 🎯

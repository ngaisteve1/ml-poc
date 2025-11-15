# 🎯 Phase 2: Alerts & Dashboard Integration

**Status:** 🎯 READY TO START  
**Timeline:** Days 3-4 (Est. 16 hours)  
**Deliverables:** 2 major components  
**Blocker:** ❌ None - can start immediately  

---

## 📋 Phase 2 Overview

Phase 2 brings drift detection from the backend into the user's hands:
1. **Alert System** - Detect drifts and trigger notifications
2. **Monitoring Dashboard** - Visualize drift trends and events

### Components to Build

```
Phase 2 Deliverables
├── alerts.py (NEW)
│   ├── AlertManager class
│   ├── Alert thresholds
│   ├── Event-to-alert mapping
│   └── Notification methods
│
└── streamlit_app.py (MODIFY)
    ├── Add Monitoring tab
    ├── Drift visualization
    ├── Event history display
    ├── Alert indicators
    └── Trend charts
```

---

## 📚 Component 1: Alert System

### File: `src/monitoring/alerts.py`

**Purpose:** Manage alerts based on drift detection results

**Key Features:**
- Define alert thresholds for different severity levels
- Convert drift detection results to alerts
- Log alerts to database
- Send notifications (console, email, dashboard)
- Track alert state (active, resolved, acknowledged)

---

## 📋 AlertManager Specification

### Class: `AlertManager`

```python
class AlertManager:
    """
    Manages alerts based on drift detection results
    
    Responsibilities:
    - Create alerts from drift detection
    - Track alert state
    - Send notifications
    - Persist alerts to database
    """
    
    def __init__(
        self,
        db: PredictionsDB,
        z_score_threshold: float = 2.0,
        ks_p_value_threshold: float = 0.05,
        trend_change_threshold: float = 10.0
    ):
        """Initialize alert manager with thresholds"""
        
    def create_alert_from_drift(
        self,
        drift_results: Dict,
        prediction_date: str
    ) -> Optional[Dict]:
        """
        Create alert from drift detection results
        
        Returns:
        {
            'alert_type': 'anomaly' | 'distribution_drift' | 'trend_drift',
            'severity': 'info' | 'warning' | 'critical',
            'message': str,
            'details': Dict,
            'recommendation': str
        }
        """
        
    def save_alert(self, alert: Dict) -> int:
        """Save alert to monitoring_events table"""
        
    def get_active_alerts(self, days: int = 7) -> pd.DataFrame:
        """Get recent alerts"""
        
    def acknowledge_alert(self, event_id: int) -> bool:
        """Mark alert as acknowledged"""
        
    def send_notification(self, alert: Dict) -> bool:
        """Send alert notification (console/email)"""
```

### Alert Levels

| Level | Threshold | Meaning | Action |
|-------|-----------|---------|--------|
| **Info** | Normal | Informational only | Log and display |
| **Warning** | Single drift signal | Possible issue | Display alert, log event |
| **Critical** | Multiple drift signals | Likely degradation | Send notification, alert user |

### Alert Types

1. **Anomaly Alert**
   - Trigger: Anomaly count > 0
   - Severity: Warning
   - Message: "Outlier detected in predictions"
   - Recommendation: "Check data quality and input features"

2. **Distribution Drift Alert**
   - Trigger: KS test p-value < 0.05
   - Severity: Warning or Critical
   - Message: "Prediction distribution has shifted"
   - Recommendation: "Consider model retraining"

3. **Trend Drift Alert**
   - Trigger: Trend change > 10%
   - Severity: Warning
   - Message: "Gradual trend change detected"
   - Recommendation: "Monitor upcoming predictions closely"

4. **Critical Multi-Signal Alert**
   - Trigger: Multiple drift signals + anomalies
   - Severity: Critical
   - Message: "Model degradation detected"
   - Recommendation: "Immediate action required - review model performance"

---

### Implementation Pattern

```python
def create_alert_from_drift(self, drift_results, prediction_date):
    """Convert drift detection to actionable alert"""
    
    if not drift_results['overall_drift_detected']:
        return None  # No alert needed
    
    alert_type = self._determine_alert_type(drift_results)
    severity = self._calculate_severity(drift_results)
    
    return {
        'alert_type': alert_type,
        'severity': severity,
        'message': self._generate_message(alert_type, drift_results),
        'details': drift_results,
        'recommendation': self._get_recommendation(alert_type),
        'prediction_date': prediction_date,
        'created_at': datetime.now().isoformat()
    }
```

---

## 🎨 Component 2: Monitoring Dashboard Tab

### File: Modifications to `src/ui/streamlit_app.py`

**Location:** Add after line 420 (in main() function)

**New Tab: "📊 Monitoring"**

### Dashboard Sections

#### 1. **Drift Status Summary** (Top)
```
Current Status: ✅ No Drift Detected (or 🔴 Drift Detected!)
├── Last Check: 2025-11-14 09:30
├── Predictions Tracked: 45
├── Active Alerts: 2
└── Last Event: 2 hours ago
```

#### 2. **Drift Indicators** (Cards)
```
┌─ Z-Score Anomalies ─┬─ Distribution Drift ─┬─ Trend Change ─┐
│ Count: 0           │ P-value: 0.87      │ Direction: ↑   │
│ Max Z: 1.2         │ Status: ✅         │ Change: +2.3%  │
│ Status: ✅         │ Mean shift: +1.2%  │ Status: ✅     │
└────────────────────┴────────────────────┴────────────────┘
```

#### 3. **Trend Chart** (Plotly Line Chart)
```
Archived GB Predictions Over Time
├── X-axis: Date (last 30 days)
├── Y-axis: Archived GB
├── Line: Predicted values
├── Color: Green (stable) → Red (drift detected)
└── Hover: Show actual vs predicted
```

#### 4. **Alerts & Events** (Table)
```
Recent Events (Last 7 days)
┌──────────────┬────────────┬─────────────────────────┐
│ Date/Time    │ Severity   │ Event                   │
├──────────────┼────────────┼─────────────────────────┤
│ 2025-11-14   │ ⚠️ Warning │ Drift detected          │
│ 09:15        │            │ Z-score: 2.3 (index 5) │
│              │            │ (More details...)       │
└──────────────┴────────────┴─────────────────────────┘
```

#### 5. **Metrics Over Time** (Multi-line Chart)
```
Model Performance Metrics (30 days)
├── R² Score trend
├── RMSE trend
├── Prediction count
└── Drift events overlay
```

#### 6. **Statistics Panel** (Metrics Display)
```
📊 Quick Stats
├── Avg Archived GB: 250.5 GB
├── Predictions w/ Actual: 15 / 45
├── Drift Events: 1
├── Last 7 Days: 3 events
└── Last 30 Days: 5 events
```

---

### Streamlit Implementation Code Structure

```python
# In src/ui/streamlit_app.py, after existing tabs:

if st.sidebar.button("📊 Monitoring"):
    st.header("🔍 Monitoring & Drift Detection")
    
    # Import monitoring components
    from src.monitoring import PredictionsDB, DriftDetector
    from src.monitoring.alerts import AlertManager  # Phase 2
    
    # Initialize components
    db = PredictionsDB()
    detector = DriftDetector()
    alerts = AlertManager(db)
    
    # Get recent predictions and events
    predictions = db.get_predictions(days=30)
    events = db.get_monitoring_events(days=7)
    
    # Display sections
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Predictions Tracked", len(predictions))
    with col2:
        st.metric("Active Alerts", len(events[events['event_severity'] == 'warning']))
    with col3:
        st.metric("Drift Events", len(events[events['event_type'] == 'drift_detected']))
    
    # Drift status
    if predictions.shape[0] > 0:
        recent = predictions.head(5)
        results = detector.check_all_drifts(recent['archived_gb_predicted'].tolist())
        
        if results['overall_drift_detected']:
            st.error("🔴 DRIFT DETECTED - Review immediately")
        else:
            st.success("✅ System nominal - No drift detected")
    
    # Charts
    st.subheader("📈 Predictions Trend")
    st.line_chart(predictions[['prediction_date', 'archived_gb_predicted']].set_index('prediction_date'))
    
    # Events table
    st.subheader("⚠️ Recent Events")
    if events.shape[0] > 0:
        st.dataframe(events[['created_at', 'event_type', 'event_severity', 'message']], use_container_width=True)
    else:
        st.info("No events in the last 7 days")
    
    db.close()
```

---

## 🔄 Integration Points

### Data Flow Phase 2

```
Azure ML Predictions
        ↓
Save to DB (predictions_db.py)
        ↓
Run Drift Detection (drift_detector.py)
        ↓
Create Alerts (alerts.py) ← NEW
        ↓
Display in Dashboard (streamlit_app.py) ← MODIFIED
        ↓
User sees alerts & trends in "Monitoring" tab
```

### Function Calls Chain

```python
# In streamlit monitoring tab:

# 1. Get predictions from database
predictions = db.get_predictions(days=30)

# 2. Run drift detection on recent predictions
recent_values = predictions['archived_gb_predicted'].tail(10).tolist()
drift_results = detector.check_all_drifts(recent_values)

# 3. Create alert if drift detected
if drift_results['overall_drift_detected']:
    alert = alerts.create_alert_from_drift(drift_results, today)
    alert_id = alerts.save_alert(alert)
    alerts.send_notification(alert)

# 4. Get recent events for display
events = db.get_monitoring_events(days=7)
st.dataframe(events)
```

---

## 📝 Tasks for Phase 2

### Task 1: Create alerts.py (4 hours)
- [ ] Create `src/monitoring/alerts.py` file
- [ ] Implement `AlertManager` class
- [ ] Implement alert creation methods
- [ ] Add database persistence
- [ ] Add notification methods
- [ ] Add test section in `__main__`

### Task 2: Add monitoring tab to Streamlit (6 hours)
- [ ] Add "Monitoring" button to sidebar
- [ ] Create monitoring section in main()
- [ ] Implement drift status display
- [ ] Add trend visualization
- [ ] Add events table
- [ ] Add statistics display
- [ ] Test with sample data

### Task 3: Integration Testing (3 hours)
- [ ] Test alert creation from drift
- [ ] Test alert persistence to DB
- [ ] Test streamlit rendering
- [ ] Test with real predictions
- [ ] Verify all metrics display correctly

### Task 4: Documentation (3 hours)
- [ ] Update copilot-instructions.md with alerts patterns
- [ ] Document AlertManager usage
- [ ] Add monitoring tab usage examples
- [ ] Create troubleshooting guide

---

## 🧪 Testing Strategy

### Test 1: Alert Creation
```python
# Simulate drift and verify alert created
drift_results = {
    'overall_drift_detected': True,
    'anomalies': {'anomaly_count': 2, 'max_z_score': 2.5},
    'distribution_drift': {'has_drift': True, 'p_value': 0.03},
    'trend_drift': {'has_trend_drift': False}
}
alert = alerts.create_alert_from_drift(drift_results, '2025-11-14')
assert alert['severity'] == 'critical'
```

### Test 2: Dashboard Rendering
```python
# Verify all sections render without errors
st.header("Monitoring")
# ... all dashboard code
# Check no exceptions and display looks good
```

### Test 3: End-to-End
```python
# Full workflow: predict → detect → alert → display
predictions = db.get_predictions(days=30)
results = detector.check_all_drifts(predictions['archived_gb_predicted'].tolist())
alert = alerts.create_alert_from_drift(results, today)
alert_id = alerts.save_alert(alert)
# Verify alert in database
events = db.get_monitoring_events(days=1)
assert alert_id in events['id'].values
```

---

## 🚀 Success Criteria

✅ **Phase 2 Complete When:**
1. AlertManager creates alerts from drift results
2. Alerts persist to monitoring_events table
3. Monitoring tab displays in Streamlit dashboard
4. Drift indicators show current status
5. Trend chart shows historical data
6. Events table displays recent alerts
7. All components integrated and tested
8. No errors in dashboard with real predictions

---

## 📌 Key Implementation Notes

### AlertManager Design
- Should be stateless (can instantiate fresh each time)
- Use PredictionsDB for persistence, not local state
- Return alert dictionaries, not custom objects
- Support both saving and sending notifications

### Dashboard Tab Design
- Keep it clean and uncluttered
- Use Streamlit columns for layout
- Show actionable information (not raw numbers)
- Include time filters for different views
- Provide context with annotations

### Performance Considerations
- Cache expensive drift calculations with `@st.cache_data`
- Limit charts to 30-day window
- Use st.spinner() for longer operations
- Show loading state while checking for drift

---

## 🔗 Dependencies

**Requires Phase 1 Components:**
- ✅ `src/monitoring/predictions_db.py`
- ✅ `src/monitoring/drift_detector.py`
- ✅ `src/monitoring/__init__.py`

**Libraries Available:**
- ✅ pandas, numpy, plotly (already in requirements.txt)
- ✅ streamlit 1.31.1 (dashboard framework)
- ✅ datetime, json (stdlib)

---

## 📈 Expected Outcomes

**After Phase 2 Complete:**

1. **User sees** drift detection alerts in real-time
2. **Dashboard** shows model health metrics
3. **Events** are tracked and displayed
4. **Trends** visualized over 30-day period
5. **Notifications** inform about issues
6. **History** shows past events and resolution

**Score Impact:**
- Current: 🟩 EXCELLENT (92/100)
- After Phase 2: 🟢 OUTPERFORM (95-98/100)

---

## 🎯 Next Steps

**Ready to Start Phase 2?**

1. Review this plan
2. Start with `alerts.py` implementation
3. Test alert creation thoroughly
4. Then integrate into dashboard
5. Final testing with real predictions

**Estimated Duration:** 2 days (16 hours work)  
**Target Completion:** November 15-16, 2025  
**Next Status Update:** After Phase 2 complete


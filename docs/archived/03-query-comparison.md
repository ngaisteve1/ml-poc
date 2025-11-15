# Query 9 vs Query 10: Quick Reference

## One-Line Answer

**Query 10 is what you run. Query 9 is documentation reference.**

---

## Visual Comparison

### Query 9: Reference Dataset
```
Purpose:        Documentation (show all features available)
Format:         SQL friendly (descriptive names)
Import effort:  HIGH (requires column mapping)
ML ready:       NO
Best for:       Understanding the data structure
```

### Query 10: CSV Export Dataset ⭐
```
Purpose:        Production ML data export
Format:         CSV friendly (snake_case columns)
Import effort:  LOW (direct pandas read)
ML ready:       YES
Best for:       Actual ML model training
```

---

## Data Comparison

### Query 9 Output
```sql
MonthStart          | FilesArchivedCount | VolumeBytesArchived | VolumeBytesArchivedGB | ...
2025-01-01          | 1500               | 536870912000        | 500.00                | ...
2025-02-01          | 2000               | 715827883000        | 666.67                | ...
```

### Query 10 Output ⭐
```csv
Period,files_archived,volume_gb,storage_saved_gb,active_tenants,active_sites,...
2025-01-01,1500,500.0,120.5,5,12,...
2025-02-01,2000,666.67,180.2,6,15,...
```

**Query 10 is ready for:** `pd.read_csv('training_data.csv')`

---

## Why Run Query 10?

| Reason | Details |
|--------|---------|
| **Column Names** | snake_case works better with pandas |
| **No Type Conversion** | Already GB, not bytes |
| **Period Format** | String format prevents date parsing issues |
| **CSV Export Optimized** | Direct copy-paste to CSV |
| **Python Ready** | No data transformation needed |

---

## Why Query 9 Exists

Query 9 shows you ALL available metrics. Use it to:
- Understand what data is available
- Pick specific features for your model
- Document data lineage

But for actual export: **Use Query 10**

---

## Timeline for ML Use

```
Query 9: Read once for understanding → Pick features you need
                                    ↓
Query 10: Run for actual data extraction → Export to CSV
                                    ↓
Python: Load CSV → Preprocess → Train → Deploy
```

---

## The Confusion (Explained)

In `setup/02-data-extraction.sql` documentation:

```sql
-- Query 9
-- Used for: Direct ML model training  ← This description is misleading
```

```sql
-- Query 10
-- Used for: Direct export to CSV for ML training  ← This is the actual ML query
```

**Query 9 description should say:** "Used for: Understanding all available features"

---

## Action Items (Prioritized)

### MUST DO
- [ ] Create 6 database indexes (see `05-performance-guide.md`)
- [ ] Run Query 10
- [ ] Export to CSV

### NICE TO HAVE
- [ ] Run Queries 1-3 for exploratory analysis
- [ ] Review Query 9 to understand available features
- [ ] Document which features you'll use

### DON'T DO
- ❌ Try to use Query 9 output directly for ML
- ❌ Skip the indexes
- ❌ Run all 10 queries at once in production

---

## Code Example: Load Query 10 Data

```python
import pandas as pd

# Load Query 10 export
df = pd.read_csv('data/training_data.csv')

# This just works! (because Query 10 is CSV-optimized)
print(df.head())

# If you tried Query 9, you'd need:
# df.rename(columns={'FilesArchivedCount': 'files_archived'})  # Lots of mapping
# df['volume_gb'] = df['VolumeBytesArchived'] / 1024**3        # Type conversion
```

---

## Query Execution Time

| Query | Time | Reason | Note |
|-------|------|--------|------|
| Query 1-8 | 3-60 sec | Various complexity levels | Exploratory only |
| Query 9 | 30-45 sec | Complex joins + aggregation | Reference only |
| **Query 10** | **5-45 sec** | **Optimized structure** | **USE THIS ONE** |

---

## Final Answer

> **Q: Query 9 vs Query 10 - which one should I run?**

**A:** 
- **For ML training**: Query 10 ✅
- **For understanding data**: Query 9 (then use Query 10 for export)
- **For both**: Read Query 9 for features, run Query 10 for data

Query 10 is production-ready. Query 9 is documentation. Both have the same data, different format.

---

**Next:** Read `04-performance-faq.md` for common questions

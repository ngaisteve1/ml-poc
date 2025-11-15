# ML POC: Visual Guide & Diagrams

## Data Flow Diagram

```
SmartArchive Database
  (ArchivedFile: 1M+ rows)
         │
         ├─ Index seeks
         ├─ JOIN operations
         └─ Aggregations
         │
         ▼
   setup/01-create-indexes.sql
   (6 nonclustered indexes)
         │
         ├─ IX_ArchivedFile_Created_Archived
         ├─ IX_ArchivedFile_UniqueId
         ├─ IX_DeletedFile_Deleted
         ├─ IX_DeletedFile_UniqueId_Composite
         ├─ IX_ArchiveJob_SiteId
         └─ IX_ArchivedFile_TenantId_Archived
         │
         ▼
  setup/02-data-extraction.sql
  (Query 10: CSV Export)
         │
         ├─ 5-45 seconds (with indexes) ✅
         └─ 60-300 seconds (without indexes) ❌
         │
         ▼
    training_data.csv
    (12-24 rows × 13 columns)
         │
         ├─ Period
         ├─ files_archived
         ├─ volume_gb
         ├─ storage_saved_gb
         └─ ... 9 more columns
         │
         ▼
  src/ml/data_preprocessing.py
  (Python processing)
         │
         ├─ DataLoader
         ├─ DataPreprocessor
         ├─ Feature Engineering
         └─ DataSplitter
         │
         ▼
   ML Model Training
```

---

## Performance Comparison Chart

```
EXECUTION TIME BY SCENARIO (2M row table)
═════════════════════════════════════════════════

Without Indexes          With Indexes          Improvement
─────────────────────────────────────────────────
45 seconds      ────►    3 seconds            93% faster ✅
120 seconds     ────►    8 seconds            93% faster ✅
180 seconds     ────►   15 seconds            92% faster ✅
900 seconds     ────►   90 seconds            90% faster ✅
(15 minutes)             (1.5 minutes)

RESULT: 85-93% faster with indexes!
```

---

## Query Execution Flow

```
Query 10 (CSV Export)
├─ Step 1: Parse SQL (1 sec)
├─ Step 2: Index Seek on Created, Archived (3-5 sec)
├─ Step 3: LEFT JOIN with DeletedFile (1-3 sec)
├─ Step 4: GROUP BY aggregation (2-5 sec)
├─ Step 5: Format results (1-2 sec)
└─ Step 6: Return to client (1 sec)

TOTAL: 10-15 seconds ✅
(Without indexes: 120 seconds)
```

---

## Timeline: From Start to ML Ready

```
T+0:00   Start
  │
  ├─ T+0:05 Run CREATE_INDEXES.sql
  │         (indexes creation starts)
  │
  ├─ T+0:20 Indexes created ✅
  │
  ├─ T+0:25 Run Query 10
  │
  ├─ T+0:35 Results ready ✅
  │
  ├─ T+0:36 Export to CSV
  │
  ├─ T+0:37 CSV file created ✅
  │
  ├─ T+0:45 Load in Python
  │
  └─ T+0:50 Ready for ML training ✅

TOTAL: 50 minutes to ML-ready
(Most is waiting for index creation)
```

---

## Index Decision Tree

```
Do you have database indexes?
  │
  ├─ YES → Go to Query 10 (5-45 sec) ✅
  │
  └─ NO  → Create indexes first
           (setup/01-create-indexes.sql)
              │
              ├─ Small table (< 100K) → 2-5 min
              ├─ Medium table (100K-1M) → 5-15 min
              └─ Large table (1M+) → 10-30 min
                 │
                 └─ Then run Query 10 (5-45 sec) ✅
```

---

## Performance by Query

```
QUERY TIME ESTIMATES (With Indexes)
═════════════════════════════════════════════════

Query 1: Monthly Volume      ▓▓ 3 seconds
Query 2: File Types          ▓▓▓▓ 8 seconds
Query 3: Storage Saved       ▓▓▓▓ 8 seconds
Query 4: Job History         ▓▓▓▓▓ 15 seconds
Query 5: Tenant Performance  ▓▓▓▓▓ 12 seconds
Query 6: Weekly Trends       ▓▓▓▓ 10 seconds
Query 7: State Distribution  ▓ 2 seconds
Query 8: Size Quantiles      ▓ 4 seconds
Query 9: Consolidated        ▓▓▓▓ 12 seconds
Query 10: CSV Export (TARGET)▓▓▓▓▓ 10 seconds

TOTAL: 90 seconds (1.5 min) for all queries ✅
```

---

## File Organization Map

```
ml-poc/
├── docs/
│   ├── 01-start-here.md ..................... Read first
│   ├── 02-quick-answers.md ................. Your 3 questions
│   ├── 03-query-comparison.md .............. Query 9 vs 10
│   ├── 04-performance-faq.md ............... FAQ & troubleshooting
│   ├── 05-performance-guide.md ............. Index details
│   ├── 06-visual-guide.md .................. This file
│   └── 99-master-reference.md .............. Complete reference
│
├── setup/
│   ├── 01-create-indexes.sql ⭐ ........... Run this first
│   └── 02-data-extraction.sql .............. Query 10 for export
│
├── src/
│   └── ml/
│       └── data_preprocessing.py ........... Python utilities
│
└── data/
    └── training_data.csv ................... Output file (you create)
```

---

## Key Metrics

```
Setup Performance:
├─ Index creation: 5-30 minutes (one-time)
├─ Query 10 execution: 5-45 seconds
├─ CSV export: 30 seconds
└─ Python import: 2-5 seconds

Ongoing Performance:
├─ Monthly refresh: ~2 minutes
├─ Feature engineering: ~3 minutes
├─ Model training: Variable
└─ Total per cycle: ~5-10 minutes
```

---

## Color Legend

```
🟢 Green = Good (< 15 seconds)
🟡 Yellow = Acceptable (15-60 seconds)
🟠 Orange = Slow (60-300 seconds)
🔴 Red = Too Slow (> 300 seconds)

With Indexes: Mostly Green ✅
Without Indexes: Mostly Red ❌
```

---

**Next:** Read `99-master-reference.md` for complete details

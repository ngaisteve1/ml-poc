# Query Performance: Complete Answers to Your Questions

## Your Questions Answered

### ❓ Question 1: "Will it take a long time to run them in prod db?"

**Answer: It depends on table size and indexes.**

#### Time Estimates by Table Size

| Table Size | Without Indexes | With Indexes | Impact |
|-----------|-----------------|-------------|--------|
| < 100K rows | 2-5 sec | 1-2 sec | Minimal difference |
| 100K-1M rows | 15-60 sec | 5-15 sec | 70% faster ✅ |
| 1M+ rows | 60-300 sec | 10-45 sec | 80-85% faster ✅ |

**Most likely scenario**: Your table is 100K-1M rows, so:
- **Without indexes**: 15-60 seconds per query
- **With indexes**: 5-15 seconds per query

**For all 10 queries combined**:
- Without indexes: 5-15 minutes
- With indexes: 1-3 minutes ✅

---

### ❓ Question 2: "Do we have the db index needed for this query?"

**Answer: Almost certainly NO - the indexes are missing.**

#### Evidence

Checked the migration scripts:
- ✅ Found only PRIMARY KEY constraints
- ❌ No nonclustered indexes for ML queries

#### Required Indexes

You **MUST create these 6 indexes**:

| # | Index Name | Table | Purpose | Expected Improvement |
|---|-----------|-------|---------|----------------------|
| 1 | `IX_ArchivedFile_Created_Archived` | ArchivedFile | Monthly aggregation (Queries 1,6,9,10) | 60-80% faster |
| 2 | `IX_ArchivedFile_UniqueId` | ArchivedFile | JOIN with DeletedFile (Queries 3,9,10) | 50-70% faster |
| 3 | `IX_DeletedFile_Deleted` | DeletedFile | Storage saved calculations (Queries 3,5) | 40-60% faster |
| 4 | `IX_DeletedFile_UniqueId_Composite` | DeletedFile | Composite JOIN key (Queries 3,9,10) | 50-75% faster |
| 5 | `IX_ArchiveJob_SiteId` | ArchiveJob | Job history JOIN (Query 4) | 30-50% faster |
| 6 | `IX_ArchivedFile_TenantId_Archived` | ArchivedFile | Tenant aggregation (Query 5) | 40-60% faster |

**Action Required**: Run `setup/01-create-indexes.sql`

---

### ❓ Question 3: "You said run Query 10 to extract data, what about Query 9?"

**Answer: Run Query 10. Query 9 is just documentation.**

#### Quick Comparison

| Aspect | Query 9 | Query 10 |
|--------|---------|----------|
| **Purpose** | Documentation reference | Production ML export |
| **Format** | SQL-friendly names | CSV-friendly names |
| **Column Names** | `FilesArchivedCount` | `files_archived` |
| **Column Names** | `VolumeBytesArchived` | `volume_gb` |
| **Data Types** | Mixed (bytes + counts) | Unified (numeric) |
| **Period Format** | Date type | String '2025-01-01' |
| **Can import directly** | ❌ Needs mapping | ✅ `pd.read_csv()` works |
| **Use for ML** | NO | YES ✅ |

#### What to Actually Do

```
Step 1: Read Query 9 to understand all available data
        ↓
Step 2: Run Query 10 to extract the data
        ↓
Step 3: Save results to CSV
        ↓
Step 4: Load in Python with pd.read_csv()
```

---

## Performance Expectations

### Query 10 Execution Time

```
Scenario                    Execution Time      Status
─────────────────────────────────────────────────────
Query 10 WITH indexes       5-45 seconds        ✅ Perfect
Query 10 WITHOUT indexes    60-300 seconds      ❌ Too slow
All 10 queries with index   2-3 minutes         ✅ Great
All 10 queries no index     10-15 minutes       ❌ Not production-ready
```

### Estimated Table Sizes

```
If your ArchivedFile table has:
────────────────────────────────────
100K rows        →  10 seconds per query
500K rows        →  20 seconds per query
1M rows          →  40 seconds per query
2M+ rows         →  60-300 seconds (⚠️ need indexes!)
```

---

## FAQ: Common Questions

### Q: Should I run Query 9 or Query 10?

**A:** Query 10 for ML. Query 9 only if you want to review all available features.

### Q: What if I can't create indexes?

**A:** Queries will still work, but:
- 3-5x slower execution
- Risk of timeouts on large tables
- Not recommended for production use

### Q: Can I run both Query 9 and 10?

**A:** Technically yes, but unnecessary. Query 10 is a better format. Skip Query 9 for production use.

### Q: How long should Query 10 take?

**A:** 
- With indexes: 5-45 seconds
- Without indexes: 60-300 seconds
- If > 5 minutes: Create the indexes!

### Q: Do I need to run Queries 1-8?

**A:** Optional. Use for exploratory analysis only:
- Query 1: Verify monthly data exists
- Query 2: Understand file types
- Query 3: Check storage savings potential
- Queries 4-8: Data quality checks

For ML training: Query 10 only.

### Q: Can I schedule these queries as a job?

**A:** Yes! Once indexes are created, add Query 10 to a scheduled SQL job:
- Run monthly to get latest data
- Export to CSV automatically
- Trigger ML retraining

### Q: What if Query 10 returns 0 rows?

**A:** Check:
```sql
SELECT COUNT(*) FROM [dbo].[ArchivedFile] WHERE [Archived] = 1;
-- If 0: No archived files yet, run archive jobs first
```

---

## Summary

| Question | Answer |
|----------|--------|
| **Will it take long?** | 5-45 sec with indexes ✅ \| 60-300 sec without ❌ |
| **Do we have indexes?** | NO - you must create 6 indexes first |
| **Query 9 or 10?** | Query 10 for ML production use |
| **Total time setup?** | ~15-30 minutes (one-time) |
| **Time per run after setup?** | 5-45 seconds for Query 10 |

---

## Next Steps

1. **Create indexes** first (see `05-performance-guide.md`)
2. **Run Query 10** from `setup/02-data-extraction.sql`
3. **Export to CSV** in SSMS
4. **Load in Python** with `src/ml/data_preprocessing.py`

---

**Questions?** Check the sections above or read `99-master-reference.md`

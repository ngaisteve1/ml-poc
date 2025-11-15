# Mock Data Generation Guide

## Overview

Before touching the production database, you can safely test the entire ML POC workflow with **realistic mock data**. This guide shows how to generate synthetic archive data that mimics the real Query 10 output.

## Why Use Mock Data?

✅ **Safe testing** - No production DB access needed  
✅ **Fast iteration** - Generate data instantly  
✅ **Reproducible** - Same seed = same data  
✅ **Customizable** - Adjust size, date range, patterns  
✅ **Full workflow** - Test all steps (Python → ML → API)

## Quick Start (1 minute)

### Step 1: Generate Mock Data
```bash
python src/ml/generate_mock_data.py
```

**Output:**
- ✅ Generated 24 months of mock data
- 📁 Saved to: `data/training_data.csv`
- 📊 File size: ~2-3 KB

### Step 2: Verify It Works
```python
from src.ml.data_preprocessing import DataLoader

df = DataLoader().load('data/training_data.csv')
print(df.head())
print(df.shape)  # Should be (24, 13)
```

### Step 3: Continue With ML Workflow
```python
from src.ml.data_preprocessing import DataPreprocessor

preprocessor = DataPreprocessor(df)
df_processed = preprocessor.create_all_features()
X, y = preprocessor.get_features_and_target(target='volume_gb')
print(f"Features shape: {X.shape}")
```

## Mock Data Features

### Realistic Patterns Included

1. **Growth Trend**
   - 2% month-over-month growth
   - Represents typical business expansion
   ```
   Month 1: 10,000 files
   Month 6: 11,045 files
   Month 12: 12,200 files
   Month 24: 14,900 files
   ```

2. **Seasonal Patterns**
   - Summer peak (June-August): +30%
   - Winter low (December-January): -30%
   - Realistic for most organizations

3. **Random Variation**
   - ±15% daily variation
   - Simulates real-world unpredictability

4. **File Type Distribution**
   - PDF: 35-45% (documents, scans)
   - Word (DOCX): 25-35% (reports, proposals)
   - Excel (XLSX): 15-25% (data, analysis)
   - Other: Remainder

5. **Storage Metrics**
   - Average file size: 5-10 MB
   - Largest files: 15-80 MB
   - Storage savings: 40-60% of archived volume
   - Deletion rate: 70-90% of archived files

6. **Archive Operations**
   - 150-200 archive jobs per day
   - 15-25 active tenants
   - 80-150 sites per tenant

## CSV Output Format

The generated CSV has 13 columns (exactly matching Query 10):

```
period,files_archived,volume_gb,avg_file_size_mb,largest_file_mb,pct_pdf,pct_docx,pct_xlsx,archive_frequency_per_day,storage_saved_gb,deleted_files_count,tenant_count,site_count
2023-01-01,10234,52.34,5.12,40.23,0.3847,0.2934,0.1923,152.3,21.44,7164,18,105
2023-02-01,10856,55.67,5.13,41.12,0.3921,0.2876,0.1891,158.9,22.12,7600,19,112
...
```

### Column Descriptions

| Column | Type | Range | Description |
|--------|------|-------|-------------|
| period | string | YYYY-MM-01 | Month start date |
| files_archived | int | 5K-20K | Files archived in month |
| volume_gb | float | 25-100 GB | Total archive volume |
| avg_file_size_mb | float | 3-8 MB | Average file size |
| largest_file_mb | float | 20-80 MB | Largest file in month |
| pct_pdf | float | 0.35-0.45 | PDF percentage |
| pct_docx | float | 0.25-0.35 | Word doc percentage |
| pct_xlsx | float | 0.15-0.25 | Excel percentage |
| archive_frequency_per_day | float | 100-250 | Jobs/day |
| storage_saved_gb | float | 10-60 GB | Storage freed |
| deleted_files_count | int | 3K-18K | Files deleted |
| tenant_count | int | 15-25 | Active tenants |
| site_count | int | 80-150 | Active sites |

## Advanced Usage

### Generate More Data (36 months)
```bash
python src/ml/generate_mock_data.py --rows 36
```

### Custom Output Location
```bash
python src/ml/generate_mock_data.py --output my_data/test_data.csv
```

### Specific Date Range
```bash
python src/ml/generate_mock_data.py --start-date 2022-01-01 --rows 36
```

### Different Random Seed (Different Data)
```bash
python src/ml/generate_mock_data.py --seed 999
```

### All Options Combined
```bash
python src/ml/generate_mock_data.py \
  --output data/test_2024.csv \
  --rows 24 \
  --start-date 2024-01-01 \
  --seed 123
```

## Using Mock Data in Your Workflow

### Option 1: Quick Testing
```python
# Step 1: Generate mock data
import subprocess
subprocess.run(["python", "src/ml/generate_mock_data.py"])

# Step 2: Load and preprocess
from src.ml.data_preprocessing import DataLoader, DataPreprocessor
df = DataLoader().load('data/training_data.csv')
preprocessor = DataPreprocessor(df)
X, y = preprocessor.get_features_and_target(target='volume_gb')

# Step 3: Train model
from sklearn.ensemble import RandomForestRegressor
model = RandomForestRegressor()
model.fit(X, y)
```

### Option 2: Full ML Pipeline
```bash
# 1. Generate mock data
python src/ml/generate_mock_data.py

# 2. Run training script
python src/ml/train.py --out_dir models

# 3. Make predictions
# ... See train.py output
```

### Option 3: API Testing
```bash
# 1. Generate mock data
python src/ml/generate_mock_data.py

# 2. Start API
uvicorn src.app.main:app --reload

# 3. Test predictions
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [{
      "month": "2025-01-01",
      "total_files": 120000,
      "avg_file_size_mb": 5.2,
      "pct_pdf": 0.40,
      "pct_docx": 0.30,
      "pct_xlsx": 0.20,
      "archive_frequency_per_day": 180
    }]
  }'
```

## Workflow: From Mock Data to Production

### Phase 1: Development (with mock data) ✅
```
1. Generate mock data: python src/ml/generate_mock_data.py
2. Develop features: Modify data_preprocessing.py
3. Train models: python src/ml/train.py
4. Test API: uvicorn src.app.main:app
```

### Phase 2: Validation (with production data)
```
1. Run Query 10: setup/02-data-extraction.sql
2. Export to CSV: data/training_data.csv
3. Run same workflow with real data
4. Compare results: Mock vs Real performance
```

### Phase 3: Production (continuous)
```
1. Monthly job: Run Query 10
2. Export CSV: data/training_data.csv
3. Retrain model: python src/ml/train.py
4. Deploy: Updated model to API
```

## Understanding the Data

### Sample Statistics (24 months)
```
Total files archived: ~285,000
Total volume: ~1,200 GB
Average monthly volume: ~50 GB
Peak month volume: ~65 GB (July)
Low month volume: ~35 GB (January)
Total storage saved: ~500 GB
Average file size: 5.2 MB
```

### Data Characteristics
- **Trend:** Consistent 2% monthly growth
- **Seasonality:** 30% variance by season
- **Noise:** ±15% random daily variation
- **Completeness:** No missing values
- **Realism:** Matches typical archive patterns

## Troubleshooting

### Q: "No such file or directory: data/training_data.csv"
```bash
# Solution: Create data directory first
mkdir data
python src/ml/generate_mock_data.py
```

### Q: "Module not found: src.ml"
```bash
# Solution: Ensure you're in ml-poc root directory
cd c:\dotnet\Navoo\Navoo.SmartArchive.Github\ml-poc
python src/ml/generate_mock_data.py
```

### Q: "How do I use this data with pandas?"
```python
import pandas as pd

# Option 1: Direct load
df = pd.read_csv('data/training_data.csv')

# Option 2: With DataLoader helper
from src.ml.data_preprocessing import DataLoader
df = DataLoader().load('data/training_data.csv')
```

### Q: "Can I modify the data generation?"
```python
# Edit src/ml/generate_mock_data.py
# Change these parameters:
base_files = 15_000        # Increase file count
seasonal_factor = 1.5      # More seasonal variation
growth_factor = 1 + (month_idx * 0.05)  # 5% growth instead of 2%
```

## Next Steps

1. ✅ Generate mock data: `python src/ml/generate_mock_data.py`
2. ✅ Load with DataLoader: Check `src/ml/data_preprocessing.py`
3. ✅ Train model: `python src/ml/train.py --out_dir models`
4. ✅ Test API: `uvicorn src.app.main:app --reload`
5. ✅ When ready: Switch to real Query 10 data

## Additional Resources

- See `01-start-here.md` for quick reference
- See `04-performance-faq.md` for common questions
- See `setup/02-data-extraction.sql` for Query 10 (production)
- See `src/ml/data_preprocessing.py` for data processing utilities

---

**Safe, fast, and realistic testing without production DB access!** 🚀

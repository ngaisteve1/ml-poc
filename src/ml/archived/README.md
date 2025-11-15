# Archived Python Files

This folder contains previous versions, experimental code, and legacy scripts that are no longer part of the active ML pipeline.

## 📋 File Descriptions

### Data Handling
**`data_preprocessing.py`** (Deprecated)
- Legacy data preprocessing utilities
- Replaced by: `src/ml/pipeline_components/prepare_data.py`
- Status: Archived (use pipeline_components instead)

**`generate_mock_data.py`** (Experimental)
- Mock data generation for testing
- Purpose: Was used for development and testing
- Status: Archived (refer to pipeline_components for actual data prep)

### Model Training
**`train.py`** (Deprecated)
- Original training script
- Replaced by: `src/ml/pipeline_components/train_model.py`
- Status: Archived (use pipeline_components instead)

**`train_with_mlflow.py`** (Legacy)
- Training with MLflow integration (old approach)
- Replaced by: `src/ml/pipeline_components/train_model.py` with MLflow
- Status: Archived

### Model Management
**`register_model.py`** (Old Location)
- Old location of model registration
- Replaced by: `src/ml/pipeline_components/register_model.py`
- Status: Archived (moved to pipeline_components)

**`score.py`** (Experimental)
- Scoring/prediction utilities
- Purpose: Used for model evaluation
- Status: Archived

### Analysis & Monitoring
**`compare_models.py`** (Experimental)
- Model comparison and evaluation
- Purpose: Compare different model versions
- Status: Archived (can be resurrected if needed for model comparison tasks)

**`monitor.py`** (Legacy)
- Monitoring utilities
- Purpose: Track model performance
- Status: Archived (use Azure ML monitoring instead)

---

## 🔄 Migration Guide

If you need functionality from archived files, use these active replacements:

| Archived File | Use Instead | Location |
|---------------|------------|----------|
| `data_preprocessing.py` | `prepare_data.py` | `src/ml/pipeline_components/` |
| `train.py` | `train_model.py` | `src/ml/pipeline_components/` |
| `train_with_mlflow.py` | `train_model.py` | `src/ml/pipeline_components/` |
| `register_model.py` | `register_model.py` | `src/ml/pipeline_components/` |
| `generate_mock_data.py` | Test data in `test_data/` | `test_data/` |
| `compare_models.py` | MLflow UI or Azure ML | See docs |
| `score.py` | Endpoint testing script | `scripts/test_endpoint_production.py` |
| `monitor.py` | Azure ML monitoring | `docs/guides/DEPLOYMENT_GUIDE.md` |

---

## 📁 Folder Structure

```
src/ml/archived/
├── README.md (this file)
├── compare_models.py
├── data_preprocessing.py
├── generate_mock_data.py
├── monitor.py
├── register_model.py
├── score.py
├── train.py
└── train_with_mlflow.py

src/app/archived/
├── __main__.py
```

---

## ✅ Active Alternatives

### Core ML Pipeline (Actively Maintained)
```
src/ml/pipeline_components/
├── prepare_data.py          ✅ Use for data prep
├── train_model.py           ✅ Use for training
└── register_model.py        ✅ Use for registration
```

### Orchestration (Actively Maintained)
```
src/ml/
├── azure_ml_pipeline.py     ✅ Use for full pipeline
```

### Utilities (Actively Maintained)
```
scripts/
├── setup/
│   └── register_environment.py   ✅ Use for setup
├── promote_model_to_azure.py     ✅ Use for deployment
└── test_endpoint_production.py   ✅ Use for testing
```

---

## 🔍 When to Check Archived Files

You might look in archived files if:

1. **Understanding older approaches:**
   - How the project evolved
   - Different implementation strategies
   - Historical context

2. **Recovering functionality:**
   - Need specific utilities that were removed
   - Want to see different implementations
   - Research previous approaches

3. **Troubleshooting:**
   - Compare with old working versions
   - Debug issues from previous implementations

---

## 🚀 Restoring Archived Files

If you need to restore a file from archive:

```bash
# Move back to active location
mv src/ml/archived/my_file.py src/ml/

# Or for pipeline components
mv src/ml/archived/my_file.py src/ml/pipeline_components/
```

Then update imports and references as needed.

---

## 📖 Documentation

For current approaches, see:
- **Quick Start:** `docs/getting-started/02-QUICK-START.md`
- **Pipeline Guide:** `docs/guides/AZURE_ML_PIPELINE_GUIDE.md`
- **Command Reference:** `docs/guides/COMMAND_REFERENCE.md`
- **Python Organization:** `PYTHON_FILES_ORGANIZATION.md`

---

## ⚠️ Important Notes

⚠️ **These files are archived, not deleted**
- They're preserved for historical reference
- Safe to keep indefinitely
- Won't interfere with current operations

✅ **Use active alternatives**
- `src/ml/pipeline_components/` has latest versions
- `scripts/` has all current utilities
- These receive updates and maintenance

---

**Last Updated:** November 13, 2025  
**Status:** Archived - Use active alternatives  
**Impact:** No impact on current operations

📂 Safe to keep. Safe to ignore. Use active files instead.

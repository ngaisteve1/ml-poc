# Python Files Organization Guide

## 📊 Current Structure Analysis

### Overview
The project has Python files organized into **two distinct purposes**, which should remain separate:

```
ml-poc/
├── scripts/                          (Deployment & Utility Scripts)
│   ├── setup/
│   │   └── register_environment.py   (Azure ML environment setup)
│   ├── promote_model_to_azure.py     (Deploy model to endpoint)
│   ├── test_endpoint_production.py   (Validate deployment)
│   └── README.md
│
└── src/ml/                          (ML Pipeline & Training)
    ├── pipeline_components/
    │   ├── prepare_data.py           (Data preparation step)
    │   ├── train_model.py            (Model training step)
    │   └── register_model.py         (Model registration step)
    ├── azure_ml_pipeline.py          (Pipeline orchestration)
    ├── archived/                     (Previous/experimental code)
    ├── __init__.py
    ├── environment.yml
    └── deployment_config.yaml
```

---

## 🎯 Why Keep Them Separate?

### `scripts/` Folder Purpose
**Utility & Deployment Scripts** - One-off tools for specific tasks

| File | Purpose | Usage | User |
|------|---------|-------|------|
| `setup/register_environment.py` | Register Azure ML environment | Manual setup step | DevOps/Admin |
| `promote_model_to_azure.py` | Deploy trained model | Post-training deployment | ML Engineer |
| `test_endpoint_production.py` | Verify endpoint health | Monitoring/validation | DevOps |

**Characteristics:**
- Run once or periodically
- External tool/utility nature
- Not part of core pipeline
- Different invocation patterns

### `src/ml/` Folder Purpose
**Core ML Pipeline** - Repeatable training and preprocessing steps

| File | Purpose | Usage | User |
|------|---------|-------|------|
| `pipeline_components/prepare_data.py` | Prepare training data | Part of pipeline | ML Engineer |
| `pipeline_components/train_model.py` | Train the model | Part of pipeline | ML Engineer |
| `pipeline_components/register_model.py` | Register trained model | Part of pipeline | ML Engineer |
| `azure_ml_pipeline.py` | Orchestrate entire pipeline | End-to-end orchestration | ML Engineer |

**Characteristics:**
- Repeatable workflow steps
- Part of standard pipeline
- Version controlled together
- Called sequentially in pipeline

---

## 📋 Essential Files Summary

### Active Core ML Files (in `src/ml/`)
✅ **src/ml/pipeline_components/prepare_data.py**
- Prepares data for training
- Called in documented workflows
- Part of main pipeline

✅ **src/ml/pipeline_components/train_model.py**
- Trains the ML model
- Called in documented workflows
- Core training step

✅ **src/ml/pipeline_components/register_model.py**
- Registers model with MLflow/Azure ML
- Called in documented workflows
- Model registration step

✅ **src/ml/azure_ml_pipeline.py**
- Orchestrates entire pipeline
- Called for end-to-end execution
- Main entry point for pipeline

### Active Utility Scripts (in `scripts/`)
✅ **scripts/setup/register_environment.py**
- Setup and initialization
- One-time or infrequent execution
- Infrastructure preparation

✅ **scripts/promote_model_to_azure.py**
- Post-training deployment
- Deploy to Azure endpoint
- Production deployment

✅ **scripts/test_endpoint_production.py**
- Monitor/validate deployment
- Testing utility
- Health checks

---

## 🗂️ Archived Python Files

All experimental, legacy, or non-essential files have been archived:

### In `src/ml/archived/`
- `compare_models.py` - Model comparison experiments
- `data_preprocessing.py` - Legacy preprocessing
- `generate_mock_data.py` - Mock data generation
- `monitor.py` - Legacy monitoring
- `register_model.py` - Old registration approach
- `score.py` - Scoring utilities
- `train_with_mlflow.py` - Legacy training
- `train.py` - Original training script

### In `src/app/archived/`
- `__main__.py` - Legacy app entry point

---

## 🚀 When to Use Each

### Use `src/ml/` Pipeline Files
```bash
# Standard workflow
python src/ml/pipeline_components/prepare_data.py --output_data ./data
python src/ml/pipeline_components/train_model.py --input_data ./data --output_model ./model
python src/ml/pipeline_components/register_model.py --input_model ./model

# Or full orchestration
python src/ml/azure_ml_pipeline.py
```

**When:** Training new models, experimenting, iterating

### Use `scripts/` Utility Scripts
```bash
# Setup (one-time)
python scripts/setup/register_environment.py

# Deployment
python scripts/promote_model_to_azure.py --model ./model

# Testing
python scripts/test_endpoint_production.py --endpoint https://...
```

**When:** Deployment, monitoring, infrastructure setup

---

## 💡 Design Rationale

### Separation of Concerns
- **`src/ml/`** = Training & experimentation logic
- **`scripts/`** = Operational & deployment tools

### Import Clarity
```python
# From pipeline components
from src.ml.pipeline_components import prepare_data

# From utility scripts
from scripts import test_endpoint_production
```

### Maintenance Benefits
- Core ML code stays in `src/` (standard Python package structure)
- Operational scripts in `scripts/` (standard automation pattern)
- Clear separation for different users (data scientists vs DevOps)

### Scalability
- Easy to add new pipeline components: `src/ml/pipeline_components/new_step.py`
- Easy to add new utility scripts: `scripts/new_utility.py`
- Archived files don't clutter active directories

---

## 📂 File Location Reference

| File | Location | Type | Purpose |
|------|----------|------|---------|
| prepare_data.py | `src/ml/pipeline_components/` | Pipeline | Data prep |
| train_model.py | `src/ml/pipeline_components/` | Pipeline | Model training |
| register_model.py | `src/ml/pipeline_components/` | Pipeline | Model registration |
| azure_ml_pipeline.py | `src/ml/` | Orchestration | Full pipeline |
| register_environment.py | `scripts/setup/` | Utility | Environment setup |
| promote_model_to_azure.py | `scripts/` | Utility | Model deployment |
| test_endpoint_production.py | `scripts/` | Utility | Endpoint testing |

---

## 🔄 Common Workflows

### Workflow 1: Local Training (Experimental)
```bash
cd ml-poc
python src/ml/pipeline_components/prepare_data.py --output_data ./test_data
python src/ml/pipeline_components/train_model.py --input_data ./test_data --output_model ./test_model
python src/ml/pipeline_components/register_model.py --input_model ./test_model
```
**Files:** All in `src/ml/pipeline_components/`

### Workflow 2: Full Pipeline Execution
```bash
cd ml-poc
python src/ml/azure_ml_pipeline.py
```
**Files:** `src/ml/azure_ml_pipeline.py` + all components

### Workflow 3: Production Deployment
```bash
# Training (in src/ml/)
python src/ml/azure_ml_pipeline.py

# Deployment (in scripts/)
python scripts/setup/register_environment.py
python scripts/promote_model_to_azure.py --model ./trained_model

# Validation (in scripts/)
python scripts/test_endpoint_production.py --endpoint <URL>
```
**Files:** Combination of `src/ml/` and `scripts/`

---

## 🎯 Recommendations

### ✅ DO KEEP SEPARATE
- Keep `scripts/` for deployment/utility functions
- Keep `src/ml/` for training/pipeline logic
- This follows Python packaging best practices

### ✅ DO CONSOLIDATE WITHIN FOLDERS
- All pipeline steps in `src/ml/pipeline_components/` ✓
- All utilities in `scripts/` with subfolders ✓
- All archived code in `archived/` subfolders ✓

### ✅ DO DOCUMENT
- Each folder has clear purpose
- README files explain usage
- Comments in code explain parameters

### ❌ DON'T
- Don't move scripts into src/ml/ (breaks separation of concerns)
- Don't mix pipeline and utility code
- Don't create sibling folders (stick with current structure)

---

## 📖 See Also

- **Project Structure:** `PROJECT_STRUCTURE.md`
- **Scripts Guide:** `scripts/README.md`
- **Quick Start:** `docs/getting-started/02-QUICK-START.md`
- **Command Reference:** `docs/guides/COMMAND_REFERENCE.md`

---

**Status:** ✅ Python files properly organized  
**Structure:** Clear separation of concerns  
**Scalable:** Easy to add new files  
**Maintainable:** Clear purposes for each folder  

🎉 **Python organization is optimal!** 🎉

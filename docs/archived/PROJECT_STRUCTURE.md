# ML POC Project Structure

Complete project organization with all directories and their purposes.

## 📁 Root Directory Structure

```
ml-poc/
├── 📄 README.md                          # Project overview
├── 📄 DOCUMENTATION_INDEX.md             # Doc index (legacy)
├── 📄 DOCUMENTATION_ORGANIZATION.md      # Documentation organization guide
├── 📄 PROJECT_STRUCTURE.md               # This file
├── 📁 docs/                              # 📚 All documentation (see below)
├── 📁 config/                            # ⚙️ Configuration files
├── 📁 scripts/                           # 🚀 Utility scripts
├── 📁 src/                               # 💻 Source code
├── 📁 data/                              # 📊 Data files
├── 📁 tests/                             # 🧪 Unit tests
├── 📁 test_data/                         # 📋 Test data samples
├── 📁 test/                              # 🔍 Integration tests
├── 📁 Terraform/                         # 🌍 Infrastructure as code
├── 📁 azure-functions-api/               # ☁️ Azure Functions
├── 📁 setup/                             # 🔧 Setup scripts
├── 📁 mlruns/                            # 📈 MLflow experiment runs
├── 📁 mlartifacts/                       # 📦 MLflow artifacts
├── 🔧 .env                               # Environment variables (local)
├── 🔧 .env.example                       # Environment template
├── 📝 .gitignore                         # Git ignore rules
└── 🔧 .venv/ / venv/                     # Python virtual environments
```

---

## 📚 Documentation (`docs/`)

Comprehensive guides organized by category.

```
docs/
├── README.md                             # 📖 Overview & navigation hub
├── getting-started/                      # 🚀 Quick entry points (4 docs)
│   ├── 01-START-HERE.md
│   ├── 02-QUICK-START.md
│   ├── 02-RUBRIC-START-HERE.md
│   └── 03-QUICK-REFERENCE.md
├── guides/                               # 📋 Procedural guides (7 docs)
│   ├── AZURE_ML_INTEGRATION_COMPLETE.md
│   ├── AZURE_ML_PIPELINE_GUIDE.md
│   ├── COMMAND_REFERENCE.md
│   ├── CSHARP_INTEGRATION_GUIDE.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── ML_POC_STATUS.md
│   └── PROJECT_STATUS.md
├── references/                           # 🔍 Technical details (8 docs)
│   ├── AI_INTEGRATION_POC.md
│   ├── ASSESSMENT_COMPLETE.md
│   ├── CURRENT_ASSESSMENT.md
│   ├── ML_USECASE_ANALYSIS.md
│   ├── POC_ASSESSMENT_RUBRIC.md
│   ├── PREDICTIVE_ANALYTICS_DEEP_DIVE.md
│   ├── README_ASSESSMENT.md
│   └── REQUIREMENTS.md
└── archived/                             # 📦 Historical (30+ docs)
    └── [Previous phase documentation]
```

**Start:** Read `docs/README.md` for documentation overview

---

## ⚙️ Configuration (`config/`)

All configuration files in one place.

```
config/
├── README.md                             # 📖 Configuration guide
├── azure_config.json                     # Azure ML workspace settings
├── environment.yml                       # Conda environment specification
├── pyproject.toml                        # Python project metadata
└── requirements.txt                      # Pip dependencies
```

**Purpose:** Centralized configuration management  
**See:** `config/README.md` for detailed descriptions

---

## 🚀 Scripts (`scripts/`)

Utility scripts for setup, testing, and deployment.

```
scripts/
├── README.md                             # 📖 Script documentation
├── setup/
│   └── register_environment.py           # Register Azure ML environment
├── promote_model_to_azure.py             # Deploy model to Azure endpoint
└── test_endpoint_production.py           # Test production endpoint
```

**Purpose:** Automated utilities for deployment and testing  
**See:** `scripts/README.md` for usage instructions

---

## 💻 Source Code (`src/`)

Application and ML code.

```
src/
├── ml/                                   # ML pipeline and training
│   ├── train.py                          # Model training script
│   ├── pipeline_components/
│   │   ├── prepare_data.py
│   │   ├── train_model.py
│   │   └── register_model.py
│   ├── azure_ml_pipeline.py
│   └── [other ML modules]
└── app/                                  # FastAPI application
    ├── main.py                           # FastAPI app entry point
    ├── models/
    ├── routes/
    └── [API implementation]
```

**Purpose:** Model training and API implementation  
**See:** Individual module docstrings for details

---

## 📊 Data (`data/`, `test_data/`)

Data storage and test datasets.

```
data/
├── training_data.csv                     # Historical archive data
├── processed/                            # Preprocessed data
└── [other data files]

test_data/
├── sample_*.csv                          # Test data samples
├── fixtures/                             # Test fixtures
└── [synthetic test data]
```

**Purpose:** Training data and test fixtures  
**Note:** Actual data files should be in `.gitignore` if sensitive

---

## 🧪 Tests (`tests/`, `test/`)

Test suites for code validation.

```
tests/
├── test_training.py                      # ML training tests
├── test_api.py                           # API endpoint tests
├── test_data_preprocessing.py            # Data processing tests
└── [other unit tests]

test/
├── integration/                          # Integration tests
├── fixtures/
└── [end-to-end tests]
```

**Purpose:** Code quality and validation  
**Run:** `pytest tests/` or `pytest test/`

---

## 🌍 Infrastructure (`Terraform/`)

Infrastructure as Code for Azure provisioning.

```
Terraform/
├── ml-archive-forecast/
│   ├── main.tf                           # Main infrastructure definition
│   ├── variables.tf                      # Variable definitions
│   ├── outputs.tf                        # Output values
│   ├── terraform.tfvars                  # Variable values
│   └── [other TF modules]
```

**Purpose:** Automated Azure resource provisioning  
**See:** `docs/guides/DEPLOYMENT_GUIDE.md` for deployment steps

---

## ☁️ Azure Functions (`azure-functions-api/`)

Serverless API deployment.

```
azure-functions-api/
├── function_app.py                       # Function app entry point
├── functions/
│   ├── predict_archive_volume/           # Prediction function
│   └── health_check/                     # Health check function
├── requirements.txt                      # Function dependencies
└── [Azure Functions configuration]
```

**Purpose:** Serverless model serving  
**See:** `docs/guides/DEPLOYMENT_GUIDE.md` (Option A) for details

---

## 📈 MLflow Tracking (`mlruns/`, `mlartifacts/`)

Experiment tracking and artifact storage.

```
mlruns/
├── 0/                                    # Default experiment
│   └── [run directories with metrics]
├── 1/                                    # Custom experiments
└── [more experiments]

mlartifacts/
├── [model artifacts]
├── [training outputs]
└── [logged files]
```

**Purpose:** Experiment tracking and reproducibility  
**Access:** MLflow UI: `mlflow ui`

---

## 🔧 Setup & Environment (`setup/`, `.venv/`, `venv/`)

Setup scripts and Python environments.

```
setup/
├── [setup scripts]
└── [initialization scripts]

.venv/ or venv/
└── [Python virtual environment files]
```

**Purpose:** Initial setup and isolated Python environment  
**Activate:** `venv\Scripts\Activate.ps1` (Windows) or `source venv/bin/activate` (Linux/Mac)

---

## 📋 Navigation by Purpose

### "I want to understand the project structure"
→ You're reading it! See overview above.

### "I want to get started quickly"
→ Start with `docs/README.md` → `docs/getting-started/01-START-HERE.md`

### "I want to find configuration"
→ See `config/` folder and `config/README.md`

### "I want to run scripts"
→ See `scripts/` folder and `scripts/README.md`

### "I want to understand the code"
→ See `src/` folder documentation and code comments

### "I want to run tests"
→ See `tests/` and `test/` folders

### "I want to deploy to Azure"
→ See `Terraform/` and `docs/guides/DEPLOYMENT_GUIDE.md`

### "I want to understand experiments"
→ See `mlruns/` and `docs/guides/COMMAND_REFERENCE.md` (MLflow section)

---

## 🎯 Quick File Lookup

| Need | Location | File |
|------|----------|------|
| Project overview | Root | `README.md` |
| Documentation index | Root/docs | `docs/README.md` |
| Quick start | docs | `docs/getting-started/02-QUICK-START.md` |
| All commands | docs | `docs/guides/COMMAND_REFERENCE.md` |
| Configuration | config | `config/` folder |
| Python scripts | scripts | `scripts/` folder |
| ML code | src | `src/ml/` folder |
| API code | src | `src/app/` folder |
| Tests | tests | `tests/` folder |
| Infrastructure | root | `Terraform/` folder |
| Serverless API | root | `azure-functions-api/` folder |

---

## 📊 File Count Summary

| Category | Count | Details |
|----------|-------|---------|
| **Documentation** | 50+ | 4 getting-started + 7 guides + 8 refs + 30+ archived |
| **Configuration** | 4 | JSON, YAML, TOML, TXT |
| **Scripts** | 3 | Setup, deployment, testing |
| **Source Code** | 10+ | ML pipeline + API + modules |
| **Tests** | 5+ | Unit + integration tests |
| **Data** | Variable | Training data + test data |
| **Infrastructure** | 5+ | Terraform modules |

---

## 🔄 Common Workflows by Folder

### Setup & Configuration
```
1. Read: docs/getting-started/
2. Install: config/requirements.txt
3. Configure: config/azure_config.json
4. Run: scripts/setup/
```

### Development
```
1. Edit: src/ (code)
2. Test: tests/ (validate)
3. Iterate and improve
4. Commit changes
```

### Training & Experiments
```
1. Prepare: data/ folder
2. Train: src/ml/train.py
3. Track: MLflow (mlruns/)
4. Evaluate: test results
```

### Deployment
```
1. Prepare: Terraform/
2. Deploy: terraform apply
3. Register: scripts/setup/
4. Promote: scripts/promote_model_to_azure.py
5. Test: scripts/test_endpoint_production.py
```

---

## 🔗 Related Documents

- **Quick Start:** `docs/getting-started/02-QUICK-START.md`
- **Commands:** `docs/guides/COMMAND_REFERENCE.md`
- **Configuration:** `config/README.md`
- **Scripts:** `scripts/README.md`
- **Deployment:** `docs/guides/DEPLOYMENT_GUIDE.md`
- **Documentation Organization:** `DOCUMENTATION_ORGANIZATION.md`

---

**Last Updated:** November 13, 2025  
**Version:** 1.0  
**Status:** Complete project structure documented

🎉 **Entire project is now well-organized and easy to navigate!** 🎉

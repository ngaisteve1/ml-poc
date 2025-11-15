# Configuration Files

This folder contains all configuration files for the ML POC project.

## 📋 Files

### `azure_config.json`
Azure ML workspace configuration and authentication settings.

**Usage:**
```json
{
  "subscription_id": "your-subscription-id",
  "resource_group": "your-resource-group",
  "workspace_name": "your-workspace-name",
  "compute_target": "your-compute-cluster"
}
```

**Reference:** See [`docs/guides/AZURE_ML_PIPELINE_GUIDE.md`](../docs/guides/AZURE_ML_PIPELINE_GUIDE.md)

---

### `environment.yml`
Conda environment specification for Python dependencies.

**Usage:**
```bash
# Create environment from file
conda env create -f config/environment.yml

# Activate environment
conda activate ml-poc-env
```

**Contents:**
- Python version and dependencies
- ML frameworks (scikit-learn, pandas, numpy)
- Visualization libraries
- Development tools

---

### `pyproject.toml`
Python project metadata and build configuration (PEP 518 format).

**Includes:**
- Project name and version
- Dependencies specifications
- Build system configuration
- Tool configurations (pytest, black, etc.)

**Usage:**
```bash
# Install project in development mode
pip install -e .

# Build package
python -m build
```

---

### `requirements.txt`
Pip-compatible requirements file with all Python dependencies.

**Usage:**
```bash
# Install from requirements
pip install -r config/requirements.txt

# Create virtual environment and install
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r config/requirements.txt
```

**Contents:**
- FastAPI and web framework dependencies
- ML/data science libraries
- MLflow for experiment tracking
- Azure SDK for cloud integration
- Testing and development tools

---

## 🔄 Environment Setup Workflows

### Option 1: Using Conda (Recommended)
```bash
# Create from environment.yml
conda env create -f config/environment.yml
conda activate ml-poc-env

# Verify installation
python --version
pip list | grep -E "fastapi|scikit|pandas"
```

### Option 2: Using Pip (Virtual Env)
```bash
# Create virtual environment
python -m venv ml-poc-venv

# Activate
ml-poc-venv\Scripts\Activate.ps1  # Windows PowerShell
source ml-poc-venv/bin/activate   # Linux/Mac

# Install requirements
pip install -r config/requirements.txt
```

### Option 3: Using Pip (Project Install)
```bash
# Install in development mode (uses pyproject.toml)
pip install -e .

# Install with extras if defined
pip install -e ".[dev]"
```

---

## ⚙️ Updating Dependencies

### Add a New Dependency

**Method 1: Update environment.yml (Conda)**
```yaml
dependencies:
  - new-package==1.2.3
```

**Method 2: Update requirements.txt (Pip)**
```
new-package==1.2.3
```

**Method 3: Update pyproject.toml**
```toml
dependencies = [
    "new-package>=1.2.3",
]
```

---

## 🔗 Related Configuration Files

- **Azure Configuration** → `azure_config.json`
- **Python Environment** → `environment.yml` or use venv
- **Project Metadata** → `pyproject.toml`
- **Dependencies** → `requirements.txt`

---

## 📖 See Also

- [`docs/guides/DEPLOYMENT_GUIDE.md`](../docs/guides/DEPLOYMENT_GUIDE.md) - Deployment setup
- [`docs/guides/COMMAND_REFERENCE.md`](../docs/guides/COMMAND_REFERENCE.md) - All commands
- [`scripts/setup/register_environment.py`](../scripts/setup/register_environment.py) - Environment registration script

---

**Last Updated:** November 13, 2025  
**Organization:** Configuration files grouped for easy reference

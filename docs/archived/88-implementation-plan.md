# Implementation Plan: Archive Volume & Storage Savings Forecast

**Document Date**: October 25, 2025  
**Project**: ML POC - Archive Forecast  
**Status**: In Progress

---

## Executive Summary

This document tracks progress against the [requirement.md](./requirement.md) and outlines remaining work to complete the POC. The project aims to build a machine learning model that forecasts archive volume and storage savings, deployed as a REST API on Azure.

---

## ✅ Completed Items

### 1. **Core ML Training Pipeline**
- ✅ Implemented `src/ml/train.py` with end-to-end training workflow
  - Synthetic data generation for POC demonstration
  - Feature engineering (month cyclical encoding, file type percentages)
  - MultiOutput regression model (RandomForestRegressor)
  - Train/validation split (80/20)
  - MLflow integration for experiment tracking
- ✅ Model evaluation and artifact logging
  - Outputs `model.joblib`, `model_card.json`, `feature_quantiles.json`
  - Logs metrics (MAE, R² score) to MLflow
- ✅ Data schema defined and validated
  - Input features: month, total_files, avg_file_size_mb, file type percentages, archive_frequency_per_day
  - Output targets: archived_gb_next_period, savings_gb_next_period

### 2. **REST API (FastAPI)**
- ✅ Implemented `src/app/main.py` with FastAPI endpoints
  - `/health` - Health check endpoint
  - `/predict` - Batch prediction endpoint with request validation
  - Pydantic models for strict input/output validation
  - Feature engineering parity with training pipeline
  - Model loading from disk or configured path
- ✅ Local development ready
  - Quick-start instructions in README.md
  - Can run via `uvicorn src.app.main:app --reload --port 8080`

### 3. **Azure Functions Integration**
- ✅ Basic Azure Functions structure in place
  - `azure-functions-api/` directory created
  - `host.json` configured
  - `HttpForecast/function.json` HTTP trigger binding defined
  - Ready for ASGI shim integration (Option A deployment)

### 4. **Terraform Infrastructure-as-Code**
- ✅ Terraform directory structure initialized
  - `Terraform/ml-archive-forecast/` folder created
  - `main.tf` file started for resource provisioning
  - Placeholder for Azure resource definitions (ML workspace, storage, resource group)

### 5. **Project Scaffolding**
- ✅ `pyproject.toml` - Python package metadata and dependencies defined
- ✅ `requirements.txt` - Dependencies specified
- ✅ `README.md` - Comprehensive quick-start and feature documentation
- ✅ `tests/` directory - Test infrastructure in place
- ✅ Git repository structure organized

### 3. **MLflow Experiment Tracking & Model Registry**
- ✅ Integrated into training pipeline
  - Logs parameters (algorithm, hyperparameters)
  - Logs metrics (MAE, R²)
  - Logs artifacts (model binary, model card, feature quantiles)
- ✅ Local MLflow backend configured by default
- ✅ Model registered in MLflow Model Registry
  - Model name: `archive-forecast-rf-v1` (or similar)
  - Versioned and staged appropriately
  - Ready for production deployment

---

## ✅ Completed Items (Continued)

### 4. **FastAPI Model Serving (Load from MLflow Registry)**
- ✅ Updated `src/app/main.py` to load from MLflow Registry
  - Loads model from `models:/{MODEL_NAME}/{MODEL_STAGE}` on startup
  - Uses `mlflow.pyfunc.load_model()` for generic model loading
  - Automatic fallback to disk model if MLflow unavailable
  - Added `/health` endpoint with model status checks
  - Added `/model/info` endpoint for metadata retrieval
  - Added `/reload-model` endpoint for model updates without restart
  - Structured logging with MLflow tracking URI info
  - Graceful error handling with informative messages
- ✅ Configuration via environment variables:
  - `MLFLOW_TRACKING_URI` (default: http://127.0.0.1:5000)
  - `MODEL_NAME` (default: archive-forecast-rf)
  - `MODEL_STAGE` (default: Production)
- ✅ Testing infrastructure:
  - Created `test_mlflow_api.py` with full test suite
  - Tests: health check, model info, predictions, reload
  - Sample data payload included for quick testing
- ✅ Updated `.env.example` with MLflow configuration

---

## ⏳ In Progress / Partial Items

## ⏳ In Progress / Partial Items

### 1. **Terraform Provisioning**
- 🟡 **Status**: Started, needs completion
- ⚠️ **What's needed**:
  - Complete `Terraform/ml-archive-forecast/main.tf` with:
    - Azure Resource Group
    - Azure Storage Account (for data and artifacts)
    - Azure ML Workspace (for advanced features in later phases)
  - Add `variables.tf` for parameterization
  - Add `outputs.tf` for resource reference outputs
  - Add `terraform.tfvars.example` for documentation
  - **Estimated effort**: 2-3 hours

### 2. **Azure Functions Deployment**
- 🟡 **Status**: Boilerplate in place, not integrated
- ⚠️ **What's needed**:
  - Implement ASGI shim in `azure-functions-api/HttpForecast/__init__.py`
  - Wire FastAPI `app` from `src.app.main` to Azure Functions handler
  - Test locally with Azure Functions Core Tools
  - Configure `requirements.txt` for Azure Functions runtime
  - **Estimated effort**: 2-3 hours

### 3. **Testing**
- 🟡 **Status**: Directory exists, needs implementation
- ⚠️ **What's needed**:
  - `tests/test_api_smoke.py` - Add API endpoint tests (health, predict)
  - Add training pipeline tests
  - Add feature engineering tests
  - Add validation tests for data schema
  - **Estimated effort**: 2-3 hours

---

## ❌ Not Started / Future Phases

### 1. **Streamlit UI**
- ❌ **Requirement**: Interactive web UI for scenario simulation
- 📋 **What's needed**:
  - Create `streamlit_app.py` for user-facing interface
  - Implement forms for input: month, file counts, file type distributions, archive frequency
  - Display predictions: archived GB, savings GB
  - Optional: Add charts/visualizations for trend analysis
  - Deploy to Azure App Service or Streamlit Cloud
  - **Estimated effort**: 4-6 hours

### 2. **Azure ML Pipeline Orchestration**
- ❌ **Requirement**: Advanced data prep, training, registration, deployment
- 📋 **What's needed**:
  - Create Azure ML pipeline with:
    - Data ingestion step
    - Data validation/preprocessing step
    - Model training step
    - Model evaluation step
    - Model registration step
  - Configure automated triggers (optional: GitHub Actions integration)
  - Set up model endpoints in Azure ML
  - **Estimated effort**: 8-12 hours (Phase 2)

### 3. **Model/Data Drift Monitoring**
- ❌ **Requirement**: Monitoring with Azure ML or custom MLflow
- 📋 **What's needed**:
  - Implement data drift detection (feature quantile monitoring)
  - Implement prediction drift detection (output distribution shifts)
  - Set up alerts/dashboards
  - Integrate with Azure Application Insights (optional)
  - **Estimated effort**: 6-8 hours (Phase 2+)

### 4. **CI/CD Pipeline**
- ❌ **Requirement**: GitHub Actions or Azure DevOps
- 📋 **What's needed**:
  - GitHub Actions workflows for:
    - Run tests on PR
    - Train model on main branch push
    - Deploy to Azure Functions
    - Deploy Streamlit UI
  - **Estimated effort**: 4-6 hours (Phase 2)

### 5. **Real Historical Data Integration**
- ❌ **Requirement**: Replace synthetic data with actual archive data
- 📋 **What's needed**:
  - Define data ingestion mechanism (CSV upload, database query, API call)
  - Data validation and quality checks
  - Handle missing/null values
  - Retraining pipeline with real data
  - **Estimated effort**: 3-5 hours (post-POC)

### 6. **Production Hardening**
- ❌ **Requirement**: Error handling, logging, security
- 📋 **What's needed**:
  - Implement structured logging (JSON logs)
  - Add comprehensive error handling
  - Security: API key authentication, CORS configuration
  - Performance optimization (caching, batch prediction)
  - Container deployment (Docker for API)
  - **Estimated effort**: 6-8 hours (Phase 2)

---

## 📊 Progress Summary

| Category | Completed | In Progress | Not Started | Total |
|----------|-----------|-------------|-------------|-------|
| **Core ML** | 4 | 0 | 2 | 6 |
| **Deployment** | 3 | 2 | 0 | 5 |
| **Monitoring** | 1 | 0 | 2 | 3 |
| **Infrastructure** | 1 | 1 | 0 | 2 |
| **Testing** | 2 | 0 | 0 | 2 |
| **TOTAL** | **11** | **3** | **4** | **18** |

**Overall Completion**: ~61% of identified work items (up from 53%)

---

## 🎯 Immediate Next Steps (Phase 1: MVP)

### Priority 1: Create MLflow Model Serving API (1-2 days) ⭐ CURRENT
1. Update `src/app/main.py` to load model from MLflow Registry
2. Test locally: `uvicorn src.app.main:app --reload --port 8080`
3. Verify predictions work end-to-end

### Priority 2: Get it Running Locally (1 day)
1. ✅ Verify local training works (DONE - model registered)
2. ✅ Verify API works locally (DONE - skeleton ready)
3. Test prediction endpoint with sample data

### Priority 3: Implement Tests (1 day)
1. Add API smoke tests (`tests/test_api_smoke.py`)
2. Add training pipeline tests
3. Run: `pytest -q tests/`

### Priority 4: Azure Deployment - Terraform (2-3 days)
1. Complete `Terraform/main.tf` with:
   - Resource Group
   - Storage Account
   - Azure ML Workspace (minimal)
2. Test provisioning: `terraform apply`
3. Verify resources created

### Priority 5: Azure Functions Integration (2-3 days)
1. Implement ASGI shim in `azure-functions-api/HttpForecast/__init__.py`
2. Test locally with Azure Functions Core Tools
3. Deploy to Azure via Terraform or CLI
4. Test /predict endpoint on Azure

### Priority 6: Streamlit UI (Optional for MVP, 4-6 days)
- Create basic Streamlit app
- Wire to local/remote API
- Optional: Deploy to Azure

---

## 📝 Technical Debt & Known Issues

1. **Synthetic Data Only**: Currently using generated data. Real archive data needed for production.
2. **No Input Validation**: Beyond Pydantic schema; need business rule validation (e.g., percentages sum to ≤1.0).
3. **Model Versioning**: No mechanism to swap models between API restarts; need model registry integration.
4. **Logging**: Minimal logging; structured logging needed for production.
5. **Error Handling**: Basic error messages; need more granular error categorization.
6. **Security**: No authentication on API; add API key or Azure AD for production.

---

## 📚 Key Files & Responsibilities

| File/Directory | Responsibility | Status |
|---|---|---|
| `src/ml/train.py` | Model training & MLflow logging | ✅ Complete |
| `src/ml/compare_models.py` | Model comparison tool | ✅ Complete |
| `src/app/main.py` | FastAPI API - **NEEDS MLflow integration** | 🟡 In Progress |
| `azure-functions-api/` | Azure Functions wrapper | 🟡 Partial |
| `Terraform/ml-archive-forecast/` | Infrastructure provisioning | 🟡 Partial |
| `tests/` | Unit & integration tests | 🟡 Partial |
| `streamlit_app.py` | UI (not started) | ❌ Not Started |

---

## 📞 Decision Points for Next Phase

1. **Where to deploy Streamlit?**
   - Azure App Service (integrated with Terraform)
   - Streamlit Cloud (simple, external)
   - Azure Container Instances (serverless)

2. **Real Data Source?**
   - CSV upload mechanism
   - Azure Data Lake / Storage query
   - Direct database integration

3. **Model Registry?**
   - MLflow Model Registry (free, local)
   - Azure ML Model Registry (enterprise, integrated)

4. **Monitoring Strategy?**
   - Custom MLflow metrics
   - Azure ML monitoring
   - Application Insights + custom dashboards

---

## Timeline Estimate

| Phase | Tasks | Effort | Timeline |
|-------|-------|--------|----------|
| **Phase 1 (MVP)** | Tests, Terraform, Azure Functions | 8-10 days | Current Week |
| **Phase 2 (Full POC)** | Streamlit UI, monitoring, hardening | 14-18 days | Week 2-3 |
| **Phase 3 (Production-Ready)** | Real data, CI/CD, security | 10-15 days | Week 4-5 |

---

## Success Criteria

- [ ] Local training and prediction work end-to-end
- [ ] Tests pass (>80% coverage)
- [ ] Terraform provisions all required Azure resources
- [ ] API deployed to Azure Functions and responds to requests
- [ ] Streamlit UI functional and connected to API
- [ ] MLflow tracks all training runs and metrics
- [ ] Documentation complete (deployment guide, API docs)
- [ ] No critical security or performance issues

---

## Appendix: Command Reference

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Train model
python src/ml/train.py --out_dir models

# Run API locally
uvicorn src.app.main:app --reload --port 8080

# Test prediction
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [{"month": "2025-07-01", "total_files": 120000, "avg_file_size_mb": 1.2, ...}]}'

# Run tests
pytest -q tests/
```

### Azure Deployment (Terraform)
```bash
cd Terraform/ml-archive-forecast/
terraform init
terraform plan
terraform apply
terraform destroy  # cleanup
```

---

**Last Updated**: October 25, 2025  
**Next Review**: After Phase 1 completion

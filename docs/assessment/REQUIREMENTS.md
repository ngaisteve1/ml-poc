# Features

- Use historical archive data (file sizes, types, archive frequency) to train a regression model.
- Predict:
  - How much data will be archived in the next month/quarter.
  - How much storage space will be saved.
- Deploy the model as a REST API (Azure ML or FastAPI on Azure Functions).
- Track model performance and drift (MLflow or Azure ML monitoring).

# Tech Stack

- **Python**: scikit-learn, pandas, MLflow (data processing, model training, experiment tracking)
- **Streamlit**: Interactive web UI (local or Azure deployment)
- **Azure Machine Learning Studio**:
  - ML workflow orchestration (data prep, training, deployment, monitoring)
  - Model registry and versioning
  - Experiment tracking and automated pipelines
- **Terraform**: Automated provisioning and cleanup of Azure resources (ML workspace, storage, web app, etc.)
- **Azure Storage**: Store data and model artifacts
- **GitHub Actions or Azure DevOps**: CI/CD pipeline automation (optional, for integration with Azure ML Studio)

> Develop your own Machine Learning Model with AzuQre Machine Learning
A\
# Workflow

1. **Terraform**:
    - Provision all required Azure resources (ML workspace, storage, web app)
    - Clean up resources after POC with `terraform destroy`
2. **ML Workflow in Azure ML Studio**:
    - Data ingestion and preparation
    - Model training and evaluation (Python scripts, Jupyter notebooks, or designer pipelines)
    - Model registration and deployment (as REST API or Streamlit app)
    - Model monitoring (drift, usage, feedback)
3. **UI**:
    - Streamlit app for user interaction and scenario simulation

# Business Value

- **Forecasting**: Helps IT and business teams plan storage needs and budgets.
- **Optimization**: Identifies trends and opportunities for further savings.
- **Reporting**: Provides data-driven insights for stakeholders.

# Budget

- **Azure ML Free Tier**: $0
- **Storage**: $0–$1
- **MLflow**: $0
- **Total**: ~$1

---

# Summary

A prediction POC for archive volume and space savings is practical, valuable, and easy to implement with Python and Azure ML. It demonstrates real ML Ops and can be extended for more advanced forecasting or optimization in the future.

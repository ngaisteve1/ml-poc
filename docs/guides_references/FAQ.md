# ❓ SmartArchive ML POC - Frequently Asked Questions

**Last Updated:** November 14, 2025  
**Status:** ✅ Common questions answered

---

## 🚀 Getting Started

### Q: Where do I start?
**A:** It depends on your time:
- **2 minutes** → Read `START_HERE.md`
- **15 minutes** → Follow `QUICK_START_SIMPLIFIED.md`
- **30 minutes** → Complete `AZURE_ML_PIPELINE_GUIDE.md`

**Recommended:** Start with `START_HERE.md` for a quick overview.

---

### Q: How long does setup take?
**A:** 
- **Local setup:** 15 minutes (Python environment + data prep)
- **First model training:** 10 minutes
- **Azure deployment:** 20-30 minutes
- **Total:** ~1 hour for complete setup

---

## 📊 Understanding the Setup

### Q: Why are there 2 experiments but only 1 registered model?
**A:** 
- **Experiments** = Training runs (multiple attempts, parameter tuning)
- **Registered Model** = Production version (the one you deploy)

You can have many experiments but promote only the best one to registered models. This is intentional.

**Read more:** `YOUR_QUESTIONS_ANSWERED.md`

---

### Q: Do I need to use Pipeline & Data tabs in Azure ML Studio?
**A:** 
- **Pipeline tab:** Yes, for monitoring Azure ML pipeline jobs
- **Data tabs:** No, not required for local MLflow setup

These are optional for viewing and analyzing results. Start with the **Jobs** tab to see your runs.

**Read more:** `AFTER_DEPLOYMENT_GUIDE.md` → FAQ section

---

### Q: Do I need to upload data to Azure ML?
**A:** 
**No.** Your data stays:
- Locally in `./test_data/` for development
- In your blob storage for production

Azure ML only stores metrics, models, and artifacts, not your raw data.

**Read more:** `AFTER_DEPLOYMENT_GUIDE.md`

---

## 🔄 MLflow & Models

### Q: Do I need an `evaluate.py` script for my local MLflow?
**A:** 
**No.** You don't need a separate evaluation script because:
- `train_model.py` already generates metrics (accuracy, precision, recall, etc.)
- `register_model.py` logs those metrics to MLflow
- `mlflow ui` displays all metrics for comparison

**You only need `evaluate.py` if you want to:**
- Evaluate a registered model on a separate test dataset
- Run batch predictions with custom metrics
- Compare multiple model versions side-by-side
- Integrate evaluation into an Azure ML pipeline job

For your current local POC, what you have is sufficient.

**Read more:** `COMMAND_REFERENCE.md` → Model Training section

---

### Q: How do I view my trained models?
**A:** 
1. Start MLflow UI:
```bash
mlflow ui
```
2. Open browser: `http://localhost:5000`
3. View:
   - **Experiments** → All training runs
   - **Models** → Registered models
   - **Metrics & Parameters** → Performance details

---

### Q: Can I train multiple models simultaneously?
**A:** 
**Yes.** Open separate terminal windows and run:
```bash
# Terminal 1
python src/ml/pipeline_components/train_model.py --n_estimators 50

# Terminal 2
python src/ml/pipeline_components/train_model.py --n_estimators 100

# Terminal 3
python src/ml/pipeline_components/train_model.py --n_estimators 150
```

Each runs independently and logs to the same MLflow tracking server.

---

## 🐛 Troubleshooting

### Q: I got "authentication failed" error
**A:** 
```bash
# Logout and login again
az logout
az login
# Follow browser prompt
```

---

### Q: I got "Module not found" error
**A:** 
```bash
# Reinstall dependencies
pip install --upgrade azure-ai-ml azure-identity mlflow scikit-learn pandas numpy
```

---

### Q: I got "Workspace not found" error
**A:** 
Check your `azure_config.json`:
```bash
# Verify correct values
az account show --query id              # subscription_id
az group list --query "[].name"         # resource_group
az ml workspace list -g your-rg --query "[].name"  # workspace_name
```

Then update `azure_config.json` with correct values.

---

### Q: The metrics file isn't being created
**A:** 
Check that your output directory exists:
```bash
# Create if missing
mkdir -p ./test_data/metrics

# Then run with explicit paths
python src/ml/pipeline_components/train_model.py \
  --input_data ./test_data/prepared \
  --output_model ./test_data/model \
  --metrics_output ./test_data/metrics
```

---

### Q: How do I fix "--metrics_output" errors?
**A:** 
The `--metrics_output` parameter is now optional with intelligent defaults.

**Old way (still works):**
```bash
python train_model.py --metrics_output ./test_data/metrics
```

**New way (simpler):**
```bash
python train_model.py
# Metrics automatically saved to ./metrics/
```

**Read more:** `FIX_APPLIED.md`

---

## 🚀 Deployment

### Q: How do I deploy to Azure ML?
**A:** 
1. Configure `azure_config.json` with your Azure details
2. Run pipeline:
```bash
python src/ml/azure_ml_pipeline.py
```
3. Monitor in Azure Portal → ML Studio → Jobs → Pipelines

**Read more:** `AZURE_ML_PIPELINE_GUIDE.md` → Deployment section

---

### Q: What are my deployment options?
**A:** 
3 options:
1. **REST API (Online Endpoint)** - Real-time predictions
2. **Batch Inference** - Process large datasets overnight
3. **FastAPI Web Service** - Custom web service

**Read more:** `DEPLOYMENT_GUIDE.md`

---

### Q: Can I deploy without Azure?
**A:** 
**Yes, locally only:** Use MLflow to register and serve models locally.

**For production:** Azure ML is recommended for:
- Scalability
- Monitoring & alerts
- Version control
- Team collaboration

---

## 📈 Monitoring & Operations

### Q: How do I monitor my model in production?
**A:** 
1. Go to Azure Portal → ML Studio
2. Navigate to **Endpoints** → Your endpoint
3. View **Metrics** tab:
   - Request count
   - Latency
   - Error rate
   - CPU/Memory usage

Enable **Application Insights** for detailed monitoring.

---

### Q: How do I get predictions from my deployed model?
**A:** 
**Option 1: REST API**
```bash
curl -X POST https://your-endpoint.azureml.net/score \
  -H "Content-Type: application/json" \
  -d '{"instances": [{"feature1": 1.0, "feature2": 2.0}]}'
```

**Option 2: Python SDK**
```python
from azure.ai.ml.entities import ManagedOnlineEndpoint
client = MLClient(...)
result = client.online_endpoints.invoke(
    endpoint_name="your-endpoint",
    request_file="input.json"
)
```

---

### Q: How often should I retrain my model?
**A:** 
Depends on your data drift. Recommendations:
- **Weekly** - If data changes frequently
- **Monthly** - For stable data patterns
- **On-demand** - When performance drops below threshold

Set up automated retraining in Azure ML Pipelines.

---

## 📂 File Organization

### Q: Where are my models stored?
**A:** 
- **Local models:** `./test_data/model/`
- **MLflow registry:** `./mlruns/`
- **Azure ML models:** Azure subscription (blob storage)

---

### Q: Where is my training data?
**A:** 
- **Raw data:** `./test_data/` (local, not in Git)
- **Prepared data:** `./test_data/prepared/`
- **Production data:** Your blob storage (via `azure_config.json`)

---

### Q: What data goes where?
**A:** 
```
Local Development          Production (Azure)
├── test_data/            ├── Blob Storage
│  ├── raw/               │  ├── raw data
│  └── prepared/          │  └── processed data
├── mlruns/               ├── ML Workspace
│  └── experiments/       │  ├── experiments
└── model/                │  ├── registered models
   └── saved model        │  └── endpoints
```

---

## 🔗 Documentation

### Q: Which document should I read?
**A:** 
| Your Situation | Read This |
|---|---|
| I'm new | `START_HERE.md` |
| Quick tutorial | `QUICK_START_SIMPLIFIED.md` |
| All commands | `COMMAND_REFERENCE.md` |
| Azure setup | `AZURE_ML_PIPELINE_GUIDE.md` |
| Already deployed | `AFTER_DEPLOYMENT_GUIDE.md` |
| Need help | This FAQ.md |

---

### Q: What documents are available?
**A:** 
Complete list in `DOCUMENTATION_INDEX.md` with navigation by role and task.

---

## 🎯 Common Workflows

### Q: I want to quickly test everything (5 min)
**A:** 
1. Read `START_HERE.md`
2. Run 3 commands from `QUICK_START_SIMPLIFIED.md`
3. Done!

---

### Q: I want to set up for production (1 hour)
**A:** 
1. `START_HERE.md` - Overview
2. `QUICK_START_SIMPLIFIED.md` - Local test
3. `AZURE_ML_PIPELINE_GUIDE.md` - Production setup
4. Deploy to Azure ML
5. Monitor in Azure Portal

---

### Q: I want all command options
**A:** 
Open `COMMAND_REFERENCE.md` and copy-paste what you need.

---

## ✨ Best Practices

### Q: Should I commit my models to Git?
**A:** 
**No.** Use `.gitignore`:
```
test_data/
mlruns/
*.pkl
*.joblib
```

Store models in:
- MLflow for development
- Azure ML for production

---

### Q: Should I version my data?
**A:** 
**Yes.** Use data versioning:
```bash
# Tag data version in your blob storage or local tracking
v1.0 - Initial dataset
v1.1 - Cleaned duplicates
v1.2 - Added new features
```

Document in `DATA_VERSIONS.md`

---

### Q: What's the difference between experiments and models?
**A:** 
| Aspect | Experiment | Model |
|--------|-----------|-------|
| **Purpose** | Track training runs | Deploy for predictions |
| **Quantity** | Many (100s possible) | Few (1-5 in production) |
| **Used for** | Tuning & comparison | Serving predictions |
| **Storage** | MLflow tracking | Model registry |
| **Example** | "lr=0.01, depth=5" | "smartarchive-archive-forecast v2.1" |

---

## 💡 Tips & Tricks

### Q: How do I compare multiple model versions?
**A:** 
In MLflow UI:
1. Go to **Models** tab
2. Select model name
3. View all versions
4. Compare metrics, parameters, artifacts

---

### Q: How do I rollback to a previous model?
**A:** 
```bash
# List model versions
mlflow models list

# Promote previous version to production
# (In MLflow UI, click "Transition Stage" → Production)
```

---

### Q: Can I run the entire pipeline in one command?
**A:** 
**Yes:**
```bash
cd ml-poc && \
python src/ml/pipeline_components/prepare_data.py --output_data ./test && \
python src/ml/pipeline_components/train_model.py --input_data ./test --output_model ./test/m --metrics_output ./test/mt && \
python src/ml/pipeline_components/register_model.py --input_model ./test/m --model_name test-model --metrics_input ./test/mt
```

Or use: `python src/ml/azure_ml_pipeline.py`

---

## 🆘 Still Have Questions?

| Issue | Next Step |
|-------|-----------|
| **Installation problem** | Check `COMMAND_REFERENCE.md` → Troubleshooting |
| **Azure authentication** | Check `AZURE_ML_PIPELINE_GUIDE.md` → Setup |
| **Command not working** | Check `FIX_APPLIED.md` for recent fixes |
| **Don't understand something** | Read `DOCUMENTATION_INDEX.md` for full guide list |
| **Need code examples** | Check `COMMAND_REFERENCE.md` → Code Samples |

---

**Last Updated:** November 14, 2025  
**Questions Covered:** 30+  
**Status:** ✅ Production Ready

For more details, see `DOCUMENTATION_INDEX.md` for complete guide list.

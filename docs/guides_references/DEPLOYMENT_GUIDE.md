# 🚀 Deploy Model to Azure ML Studio

**Time:** 20-30 minutes  
**Difficulty:** Intermediate  
**Status:** ✅ Ready to deploy

---

## Overview

There are three ways to deploy your model:

1. **Online Endpoint** (REST API) - Real-time predictions
2. **Batch Inference** - Large-scale batch jobs
3. **Web Service** - Custom FastAPI/Flask app

This guide covers all three.

---

## Prerequisites

Before deploying, make sure you have:

```bash
# 1. Model registered in Azure ML
python promote_model_to_azure.py \
  --model_name smartarchive-archive-forecast \
  --model_version 1 \
  --azure_model_name smartarchive-archive-forecast

# 2. Verified model locally
python src/ml/score.py
# Expected output: ✅ Test complete!

# 3. Logged into Azure
az login
az account show
```

---

## Option 1: Deploy as Online Endpoint (REST API)

This creates a real-time REST API endpoint.

### Step 1: Create Endpoint

```bash
cd ml-poc

# Create the online endpoint
az ml online-endpoint create \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep \
  --auth-mode key
```

**Expected Output:**
```
Successfully created online endpoint "archive-forecast-ep"
URL: https://archive-forecast-ep.eastus.inference.ml.azure.com/score
Key: xxx...
```

### Step 2: Create Deployment

```bash
# Deploy the model
az ml online-deployment create \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --endpoint-name archive-forecast-ep \
  --name blue \
  --model azureml:smartarchive-archive-forecast:1 \
  --code-path src/ml \
  --code-scoring-uri score.py \
  --environment-path src/ml/environment.yml \
  --instance-type Standard_F2s_v2 \
  --instance-count 1 \
  --file deployment_config.yaml
```

### Step 3: Test the Endpoint

```bash
# Get endpoint details
az ml online-endpoint show \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep

# Get the scoring URL and key
az ml online-endpoint get-credentials \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep
```

### Step 4: Make Predictions

```bash
# Create a test request file
cat > test_request.json << 'EOF'
{
  "instances": [
    {
      "month": "2025-01-01",
      "total_files": 120000,
      "avg_file_size_mb": 1.2,
      "pct_pdf": 0.45,
      "pct_docx": 0.30,
      "pct_xlsx": 0.25,
      "archive_frequency_per_day": 320
    }
  ]
}
EOF

# Test via CLI
az ml online-endpoint invoke \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep \
  --request-file test_request.json

# OR test via REST API (with curl)
ENDPOINT_URL=$(az ml online-endpoint show \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep \
  --query scoring_uri -o tsv)

KEY=$(az ml online-endpoint get-credentials \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep \
  --query primary_key -o tsv)

curl -X POST "$ENDPOINT_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d @test_request.json
```

**Expected Response:**
```json
{
  "status": "success",
  "predictions": [
    {
      "archived_gb_next_period": 1250.5,
      "savings_gb_next_period": 875.35
    }
  ],
  "instance_count": 1,
  "timestamp": "2025-11-13T12:34:56.789Z",
  "model": "RandomForest",
  "drift_detected": false
}
```

---

## Option 2: Deploy for Batch Inference

For processing large datasets.

### Step 1: Create Batch Endpoint

```bash
# Create batch endpoint
az ml batch-endpoint create \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-batch \
  --auth-mode aad_token
```

### Step 2: Create Batch Deployment

```bash
# Deploy for batch processing
az ml batch-deployment create \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --endpoint-name archive-forecast-batch \
  --name batch-1 \
  --model azureml:smartarchive-archive-forecast:1 \
  --code-path src/ml \
  --code-scoring-uri score.py \
  --environment-path src/ml/environment.yml \
  --instance-type Standard_D4s_v3 \
  --instance-count 4 \
  --compute aml-compute-batch \
  --mini-batch-size 100 \
  --output-action append_row \
  --output-file-name predictions.csv
```

### Step 3: Submit Batch Job

```bash
# Create batch request
cat > batch_request.json << 'EOF'
{
  "instances": [
    {
      "month": "2025-01-01",
      "total_files": 120000,
      "avg_file_size_mb": 1.2,
      "pct_pdf": 0.45,
      "pct_docx": 0.30,
      "pct_xlsx": 0.25,
      "archive_frequency_per_day": 320
    },
    {
      "month": "2025-02-01",
      "total_files": 125000,
      "avg_file_size_mb": 1.25,
      "pct_pdf": 0.44,
      "pct_docx": 0.31,
      "pct_xlsx": 0.25,
      "archive_frequency_per_day": 340
    }
  ]
}
EOF

# Submit batch job
az ml batch-endpoint invoke \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-batch \
  --request-file batch_request.json
```

---

## Option 3: Deploy with FastAPI (Local or Container)

For custom application deployment.

### Step 1: Create FastAPI App

Create `src/app/main.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import sys
sys.path.insert(0, '../ml')

from score import init, run

app = FastAPI(title="SmartArchive Forecast API", version="1.0.0")

# Initialize model on startup
@app.on_event("startup")
async def startup_event():
    init()

class PredictionRequest(BaseModel):
    instances: list

@app.post("/predict")
async def predict(request: PredictionRequest):
    """Make predictions"""
    try:
        raw_data = json.dumps(request.dict())
        result = run(raw_data)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}

@app.get("/")
async def root():
    """API info"""
    return {
        "name": "SmartArchive Forecast API",
        "version": "1.0.0",
        "endpoints": ["/predict", "/health"]
    }
```

### Step 2: Run Locally

```bash
# Install FastAPI
pip install fastapi uvicorn

# Run server
cd src/app
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Test Locally

```bash
# Terminal 1: Server running

# Terminal 2: Make request
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [{
      "month": "2025-01-01",
      "total_files": 120000,
      "avg_file_size_mb": 1.2,
      "pct_pdf": 0.45,
      "pct_docx": 0.30,
      "pct_xlsx": 0.25,
      "archive_frequency_per_day": 320
    }]
  }'

# Or Python
import requests
response = requests.post("http://localhost:8000/predict", json={
    "instances": [{...}]
})
print(response.json())
```

### Step 4: Deploy to Azure Container Instances (Optional)

```bash
# Build Docker image
docker build -t smartarchive-forecast:1.0 .

# Push to Azure Container Registry
az acr build --registry myregistry \
  --image smartarchive-forecast:1.0 .

# Deploy to Container Instances
az container create \
  --resource-group poc \
  --name smartarchive-forecast \
  --image myregistry.azurecr.io/smartarchive-forecast:1.0 \
  --ports 8000 \
  --cpu 1 \
  --memory 1
```

---

## Deployment Comparison

| Feature | Online Endpoint | Batch | FastAPI |
|---------|-----------------|-------|---------|
| **Use Case** | Real-time API | Large scale | Custom app |
| **Latency** | ~100ms | Minutes | ~100ms |
| **Throughput** | Low-Medium | Very High | Medium |
| **Cost** | Pay per hour | Pay per compute | Container cost |
| **Setup Time** | 5 min | 10 min | 15 min |
| **Best For** | Production API | Historical analysis | Custom workflows |

---

## Monitoring & Updating Deployment

### Monitor Endpoint

```bash
# Get metrics
az ml online-endpoint logs \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep \
  --deployment-name blue

# Get performance metrics
az ml online-endpoint get-stats \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep
```

### Update Deployment (Blue-Green)

```bash
# Create green deployment
az ml online-deployment create \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --endpoint-name archive-forecast-ep \
  --name green \
  --model azureml:smartarchive-archive-forecast:2 \
  --file deployment_config_green.yaml

# Split traffic (50/50)
az ml online-endpoint update \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep \
  --traffic "blue=50 green=50"

# Route 100% to green
az ml online-endpoint update \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep \
  --traffic "blue=0 green=100"

# Delete blue
az ml online-deployment delete \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --endpoint-name archive-forecast-ep \
  --name blue
```

---

## Troubleshooting

### "Model not found"
```bash
# Verify model is registered
az ml model list --resource-group poc --workspace-name mlflow-workspace

# Check model details
az ml model show \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name smartarchive-archive-forecast \
  --version 1
```

### "Endpoint creation failed"
```bash
# Check compute resources
az ml compute list --resource-group poc --workspace-name mlflow-workspace

# Check logs
az ml online-endpoint logs \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep
```

### "Scoring script error"
```bash
# Test score.py locally first
python src/ml/score.py

# Check for import errors
python -c "from src.ml.score import init, run; print('✅ Imports OK')"
```

---

## Success Checklist

- [ ] Model promoted to Azure ML
- [ ] `score.py` tested locally
- [ ] `environment.yml` created
- [ ] Endpoint created (or batch/app deployed)
- [ ] Test prediction successful
- [ ] Response format correct
- [ ] Monitoring enabled
- [ ] Documentation updated

---

## Next Steps

1. **Monitor in production** → Set up Application Insights
2. **Automated retraining** → Create scheduled pipeline
3. **A/B testing** → Deploy multiple models, split traffic
4. **Integration** → Connect to SmartArchive backend

---

## Quick Deployment Commands (Copy-Paste)

```bash
# 1. Prerequisites
az login
cd ml-poc

# 2. Test locally
python src/ml/score.py

# 3. Deploy as REST API
az ml online-endpoint create \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep \
  --auth-mode key

az ml online-deployment create \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --endpoint-name archive-forecast-ep \
  --name blue \
  --model azureml:smartarchive-archive-forecast:1 \
  --code-path src/ml \
  --code-scoring-uri score.py \
  --environment-path src/ml/environment.yml \
  --instance-type Standard_F2s_v2 \
  --instance-count 1

# 4. Test
az ml online-endpoint invoke \
  --resource-group poc \
  --workspace-name mlflow-workspace \
  --name archive-forecast-ep \
  --request-file test_request.json
```

---

**Status:** ✅ Ready to deploy  
**Documentation:** Complete  
**Next:** Choose deployment option and run commands above

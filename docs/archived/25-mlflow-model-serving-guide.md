# MLflow Model Serving Guide - FastAPI Integration

## Overview

You've registered your model in MLflow. Now create a FastAPI endpoint that loads and serves predictions from the MLflow Model Registry instead of loading from disk.

**Status**: Next Priority Task  
**Time Estimate**: 1-2 hours  
**Files to Update**: `src/app/main.py`

---

## Step 1: Understand MLflow Model Loading

### Current (Disk-based)
```python
import joblib
model = joblib.load('models/model.joblib')
```

### New (MLflow Registry)
```python
import mlflow
# Option A: Load specific version
model = mlflow.pyfunc.load_model(
    model_uri="models:/archive-forecast-rf/1"
)

# Option B: Load production stage
model = mlflow.pyfunc.load_model(
    model_uri="models:/archive-forecast-rf/Production"
)

# Option C: Load from run
model = mlflow.sklearn.load_model(
    model_uri="runs:/abc123/model"
)
```

---

## Step 2: Update FastAPI Main App

### Current Code Structure

Your `src/app/main.py` likely has:
```python
from fastapi import FastAPI
import joblib

app = FastAPI()

# Load model at startup
model = joblib.load('models/model.joblib')

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/predict")
async def predict(request: PredictionRequest):
    # Make prediction
    pass
```

### Updated Code (MLflow Integration)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow
from mlflow import MlflowClient
import os
from typing import List, Dict, Any

app = FastAPI(
    title="Archive Forecast API",
    description="ML model serving for archive volume and storage savings forecasting"
)

# MLflow Configuration
MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI", 
    "http://127.0.0.1:5000"  # Default: local MLflow
)
MODEL_NAME = os.getenv("MODEL_NAME", "archive-forecast-rf")
MODEL_STAGE = os.getenv("MODEL_STAGE", "Production")  # or "Staging", "1" for version

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Global model variable
model = None
model_metadata = None

def load_model():
    """Load model from MLflow Model Registry"""
    global model, model_metadata
    try:
        # Option 1: Load from Model Registry by stage
        model_uri = f"models:/{MODEL_NAME}/{MODEL_STAGE}"
        
        # Option 2: Alternative - load by version number
        # model_uri = f"models:/{MODEL_NAME}/1"
        
        # Option 3: Alternative - load from run
        # model_uri = f"runs:/run_id/model"
        
        print(f"Loading model from: {model_uri}")
        model = mlflow.pyfunc.load_model(model_uri)
        
        # Get model metadata
        client = MlflowClient(MLFLOW_TRACKING_URI)
        model_metadata = client.get_model_version_by_stage(
            MODEL_NAME, MODEL_STAGE
        )
        
        print(f"✅ Model loaded successfully: {MODEL_NAME} ({MODEL_STAGE})")
        return True
    except Exception as e:
        print(f"❌ Failed to load model: {str(e)}")
        return False

@app.on_event("startup")
async def startup_event():
    """Load model on app startup"""
    if not load_model():
        raise RuntimeError("Failed to initialize model")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown"""
    print("Shutting down...")

# Pydantic Models
class FeatureInput(BaseModel):
    """Single prediction input"""
    month: str
    total_files: int
    avg_file_size_mb: float
    largest_file_mb: float
    pct_pdf: float
    pct_docx: float
    pct_xlsx: float
    archive_frequency_per_day: float
    storage_saved_gb: float
    deleted_files_count: int
    tenant_count: int
    site_count: int

class PredictionRequest(BaseModel):
    """Batch prediction request"""
    instances: List[FeatureInput]

class PredictionResponse(BaseModel):
    """Prediction response"""
    predictions: List[Dict[str, float]]
    model_name: str
    model_stage: str
    model_version: str

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if model is None:
        return {
            "status": "unhealthy",
            "error": "Model not loaded"
        }
    
    return {
        "status": "healthy",
        "model_loaded": True,
        "model_name": MODEL_NAME,
        "model_stage": MODEL_STAGE,
        "mlflow_uri": MLFLOW_TRACKING_URI
    }

@app.get("/model/info")
async def model_info():
    """Get model metadata"""
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded"
        )
    
    return {
        "model_name": MODEL_NAME,
        "model_stage": MODEL_STAGE,
        "model_version": str(model_metadata.version) if model_metadata else "unknown",
        "tracking_uri": MLFLOW_TRACKING_URI,
        "loaded": True
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Make predictions on archive forecast
    
    Returns:
        - predictions: List of [archived_gb, savings_gb] for each input
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded"
        )
    
    try:
        # Convert requests to format model expects
        import pandas as pd
        
        data_list = []
        for instance in request.instances:
            data_list.append(instance.dict())
        
        df = pd.DataFrame(data_list)
        
        # Make predictions
        predictions = model.predict(df)
        
        # Format response
        response_data = []
        for pred in predictions:
            response_data.append({
                "archived_gb": float(pred[0]),
                "savings_gb": float(pred[1])
            })
        
        return PredictionResponse(
            predictions=response_data,
            model_name=MODEL_NAME,
            model_stage=MODEL_STAGE,
            model_version=str(model_metadata.version) if model_metadata else "unknown"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Prediction failed: {str(e)}"
        )

@app.post("/reload-model")
async def reload_model():
    """
    Reload model from MLflow Registry
    Useful when model is updated without restarting API
    """
    try:
        if load_model():
            return {
                "status": "success",
                "message": f"Model {MODEL_NAME} reloaded",
                "stage": MODEL_STAGE
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reload model"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reload failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080
    )
```

---

## Step 3: Test Locally

### Start MLflow UI
```bash
# Terminal 1: Start MLflow
mlflow ui --host 127.0.0.1 --port 5000
# Open: http://127.0.0.1:5000
```

### Run FastAPI
```bash
# Terminal 2: Start API
cd c:\dotnet\Navoo\Navoo.SmartArchive.Github\ml-poc
uvicorn src.app.main:app --reload --port 8080
```

### Test Endpoints
```bash
# Terminal 3: Test health check
curl http://localhost:8080/health

# Test model info
curl http://localhost:8080/model/info

# Test prediction
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [
      {
        "month": "2025-07-01",
        "total_files": 120000,
        "avg_file_size_mb": 1.2,
        "largest_file_mb": 250,
        "pct_pdf": 0.5,
        "pct_docx": 0.3,
        "pct_xlsx": 0.1,
        "archive_frequency_per_day": 1000,
        "storage_saved_gb": 500,
        "deleted_files_count": 5000,
        "tenant_count": 10,
        "site_count": 50
      }
    ]
  }'
```

---

## Step 4: Environment Variables

Create `.env` file in project root:

```bash
# MLflow Configuration
MLFLOW_TRACKING_URI=http://127.0.0.1:5000
MODEL_NAME=archive-forecast-rf
MODEL_STAGE=Production

# API Configuration
PORT=8080
HOST=0.0.0.0
```

Or set via command line:
```bash
$env:MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
$env:MODEL_NAME = "archive-forecast-rf"
$env:MODEL_STAGE = "Production"
uvicorn src.app.main:app --reload --port 8080
```

---

## Step 5: Handle Model Versioning

### Strategy 1: Load by Stage (Recommended)
```python
# Always load Production stage
model_uri = "models:/archive-forecast-rf/Production"
```

Advantages:
- Single endpoint always serves production model
- Update model by transitioning version to Production stage
- No API restart needed (call `/reload-model` endpoint)

### Strategy 2: Load Specific Version
```python
# Load version 2
model_uri = "models:/archive-forecast-rf/2"
```

Advantages:
- Explicit version control
- Roll back easily by changing version number

### Strategy 3: Load from Run
```python
# Load from specific experiment run
model_uri = "runs:/abc123/model"
```

Advantages:
- Direct run reference
- Useful for testing

---

## Step 6: Add Error Handling

### Handle Model Not Available
```python
@app.post("/predict")
async def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable - model loading failed"
        )
    # ... prediction logic
```

### Handle Invalid Input
```python
from pydantic import validator

class FeatureInput(BaseModel):
    month: str
    total_files: int
    
    @validator('total_files')
    def total_files_positive(cls, v):
        if v <= 0:
            raise ValueError('total_files must be positive')
        return v
```

---

## Step 7: Test with Actual Data

```python
# test_mlflow_api.py
import requests
import json

BASE_URL = "http://localhost:8080"

# Test health
response = requests.get(f"{BASE_URL}/health")
print("Health:", response.json())

# Test model info
response = requests.get(f"{BASE_URL}/model/info")
print("Model Info:", response.json())

# Test prediction
payload = {
    "instances": [
        {
            "month": "2025-07-01",
            "total_files": 100000,
            "avg_file_size_mb": 1.5,
            "largest_file_mb": 300,
            "pct_pdf": 0.4,
            "pct_docx": 0.35,
            "pct_xlsx": 0.15,
            "archive_frequency_per_day": 500,
            "storage_saved_gb": 400,
            "deleted_files_count": 3000,
            "tenant_count": 5,
            "site_count": 25
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/predict",
    json=payload,
    headers={"Content-Type": "application/json"}
)

print("Prediction:", json.dumps(response.json(), indent=2))
```

Run it:
```bash
python test_mlflow_api.py
```

---

## Troubleshooting

### Error: "Model not found in registry"
**Cause**: Model not registered or wrong name
**Fix**: 
```bash
# Check registered models in MLflow UI
# Or run:
mlflow models list
```

### Error: "Connection refused to MLflow"
**Cause**: MLflow not running
**Fix**: Start MLflow in separate terminal
```bash
mlflow ui --host 127.0.0.1 --port 5000
```

### Error: "Model load timeout"
**Cause**: Model is large or network slow
**Fix**: Increase timeout or pre-cache model

### Model predictions incorrect
**Cause**: Input features wrong format
**Fix**: Verify feature names and order match training data

---

## Next Steps After MLflow Integration

1. ✅ FastAPI loads from MLflow Registry
2. ✅ Test with predictions working
3. → **Add unit tests** (`tests/test_api_mlflow.py`)
4. → **Azure Deployment** (Functions + Terraform)
5. → **Monitoring** (track inference performance)

---

## Key Concepts

| Concept | Meaning | Example |
|---------|---------|---------|
| **Model URI** | Path to model in registry or run | `models:/archive-forecast-rf/Production` |
| **Model Stage** | Environment state | `Production`, `Staging`, `Archived` |
| **Model Version** | Numeric version | `1`, `2`, `3` |
| **MLflow Client** | Access to registry metadata | `MlflowClient()` |
| **pyfunc** | Generic model loader | `mlflow.pyfunc.load_model()` |

---

## Files to Update

- ✅ `src/app/main.py` - Add MLflow integration
- [ ] `requirements.txt` - Ensure `mlflow` is listed
- [ ] `tests/test_api_mlflow.py` - Add API tests
- [ ] `.env.example` - Document MLflow variables
- [ ] `docs/10-implementation-plan.md` - Mark as complete ✓

---

**Status**: Ready to implement  
**Estimated Time**: 1-2 hours  
**Next Review**: After implementation + testing  

---

**Questions?**
- See: `docs/08-mlflow-integration.md`
- Check: `docs/09-complete-workflow.md`
- Reference: `docs/14-model-comparison-tool.md`

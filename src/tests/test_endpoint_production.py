#!/usr/bin/env python3
"""
Azure ML Endpoint - Production Test
Uses the correct feature set discovered from model training script
"""

import os
import json
import requests
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ENDPOINT_URL = os.getenv('MLFLOW_ENDPOINT')
API_KEY = os.getenv('MLFLOW_API_KEY')

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}

print("=" * 70)
print("AZURE ML ENDPOINT - PRODUCTION TEST")
print("=" * 70)
print(f"\n🔗 Endpoint: {ENDPOINT_URL}")
print(f"🔑 Deployment: smartarchive-archive-forecast-1")

# Model expects these 9 features (from train.py build_features function)
features = [
    "total_files",
    "avg_file_size_mb",
    "pct_pdf",
    "pct_docx",
    "pct_xlsx",
    "pct_other",
    "archive_frequency_per_day",
    "month_sin",
    "month_cos"
]

# Sample data - realistic archive metrics
# Calculate month_sin and month_cos for January (month=1)
month = 1
month_sin = np.sin(2 * np.pi * month / 12)
month_cos = np.cos(2 * np.pi * month / 12)

data = {
    "input_data": {
        "columns": features,
        "index": [0],
        "data": [[
            120000,           # total_files
            1.2,              # avg_file_size_mb
            0.45,             # pct_pdf
            0.30,             # pct_docx
            0.15,             # pct_xlsx
            0.10,             # pct_other (1.0 - 0.45 - 0.30 - 0.15)
            320.0,            # archive_frequency_per_day
            month_sin,        # month_sin for January
            month_cos         # month_cos for January
        ]]
    }
}

print(f"\n📤 Request Features ({len(features)}):")
for i, feat in enumerate(features):
    print(f"   {i+1}. {feat}: {data['input_data']['data'][0][i]}")

print(f"\n🔄 Sending request to {ENDPOINT_URL}/score...")

try:
    response = requests.post(ENDPOINT_URL, json=data, headers=headers, timeout=30)
    
    print(f"\n📊 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS!")
        result = response.json()
        print(f"\n📈 Predictions:")
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        # Parse the predictions
        predictions = result[0]
        print(f"\n   Forecasted archived_gb_next_period: {predictions[0]:.2f} GB")
        print(f"   Forecasted savings_gb_next_period: {predictions[1]:.2f} GB")
        
        print(f"\n💾 Model is ready for integration!")
        
    else:
        print(f"❌ Failed with status {response.status_code}")
        try:
            error = response.json()
            print(f"Error: {json.dumps(error, indent=2)}")
        except:
            print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

"""
Azure ML Endpoint Client: SmartArchive Archive Forecasting

Handles real-time predictions by calling the Azure ML endpoint.
Replaces mock predictions with actual model predictions.

Model expects 9 features (from training):
  1. total_files - Total number of files archived
  2. avg_file_size_mb - Average file size in MB
  3. pct_pdf - Percentage of PDF files
  4. pct_docx - Percentage of DOCX files
  5. pct_xlsx - Percentage of XLSX files
  6. pct_other - Percentage of other file types
  7. archive_frequency_per_day - Daily archive frequency
  8. month_sin - Sine component of month (seasonality)
  9. month_cos - Cosine component of month (seasonality)

Returns 2 outputs:
  1. archived_gb_next_period - Forecasted archived GB
  2. savings_gb_next_period - Forecasted savings in GB
"""

import json
import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class AzureMLEndpointClient:
    """Client for calling Azure ML endpoint"""
    
    def __init__(self):
        """Initialize endpoint configuration from environment variables"""
        self.endpoint_url = os.getenv('MLFLOW_ENDPOINT')
        self.api_key = os.getenv('MLFLOW_API_KEY')
        self.deployment_name = os.getenv('MLFLOW_DEPLOYMENT')
        
        if not all([self.endpoint_url, self.api_key]):
            raise ValueError(
                "Azure ML endpoint configuration missing. "
                "Set MLFLOW_ENDPOINT and MLFLOW_API_KEY in .env file"
            )
    
    def prepare_request_payload(self, historical_df: pd.DataFrame) -> Dict:
        """
        Prepare request payload for Azure ML endpoint with 9 required features
        
        Args:
            historical_df: DataFrame with required columns for feature engineering
            Required columns: total_files, avg_file_size_mb, pct_pdf, pct_docx, 
                            pct_xlsx, pct_other, archive_frequency_per_day, and date
        
        Returns:
            Dictionary formatted for Azure ML endpoint with input_data structure
        """
        # Required features for the model
        feature_columns = [
            'total_files',
            'avg_file_size_mb',
            'pct_pdf',
            'pct_docx',
            'pct_xlsx',
            'pct_other',
            'archive_frequency_per_day'
        ]
        
        # Ensure all required columns exist
        missing_cols = set(feature_columns) - set(historical_df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Calculate month_sin and month_cos for seasonality (from date column)
        if 'date' not in historical_df.columns:
            raise ValueError("date column is required for calculating seasonality features")
        
        dates = pd.to_datetime(historical_df['date'])
        months = dates.dt.month
        
        # Calculate sine and cosine components for month (12-month cycle)
        month_sin = np.sin(2 * np.pi * months / 12)
        month_cos = np.cos(2 * np.pi * months / 12)
        
        # Build feature data with all 9 features
        feature_data = historical_df[feature_columns].values.tolist()
        
        # Add month_sin and month_cos to each row
        for i in range(len(feature_data)):
            feature_data[i].append(month_sin.iloc[i])
            feature_data[i].append(month_cos.iloc[i])
        
        # Azure ML endpoint expects input_data structure
        all_features = feature_columns + ['month_sin', 'month_cos']
        
        payload = {
            "input_data": {
                "columns": all_features,
                "index": list(range(len(feature_data))),
                "data": feature_data
            }
        }
        
        return payload
    
    def call_endpoint(self, historical_df: pd.DataFrame) -> Dict:
        """
        Call Azure ML endpoint with historical data
        
        Args:
            historical_df: DataFrame with historical data
        
        Returns:
            Dictionary with predictions and metrics from endpoint
            
        Raises:
            requests.RequestException: If endpoint call fails
        """
        try:
            payload = self.prepare_request_payload(historical_df)
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            print(f"  Payload size: {len(json.dumps(payload))} bytes")
            print(f"  Headers: Content-Type={headers['Content-Type']}, API Key length={len(self.api_key)}")
            
            response = requests.post(
                self.endpoint_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            print(f"  Status Code: {response.status_code}")
            
            # Raise exception for bad status codes
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"Azure ML endpoint timeout (30s). "
                f"Endpoint: {self.endpoint_url}"
            )
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Failed to connect to Azure ML endpoint. "
                f"Check endpoint URL and network connection. "
                f"Error: {str(e)}"
            )
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {response.status_code} Error"
            try:
                error_detail = response.json()
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {response.text}"
            
            if response.status_code == 401:
                raise PermissionError(
                    f"Authentication failed (401). Check MLFLOW_API_KEY in .env. {error_msg}"
                )
            elif response.status_code == 404:
                raise ValueError(
                    f"Endpoint not found (404): {self.endpoint_url}. {error_msg}"
                )
            elif response.status_code == 424:
                raise RuntimeError(
                    f"Failed Dependency (424). Endpoint received request but cannot process it. "
                    f"This usually means: payload format mismatch, missing input columns, or endpoint not fully deployed. "
                    f"Details: {error_msg}"
                )
            raise RuntimeError(f"{error_msg}")
    
    def get_predictions(
        self, 
        historical_df: pd.DataFrame,
        forecast_days: int = 90
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Get predictions from Azure ML endpoint
        
        Args:
            historical_df: Historical data for input features (must have date column)
            forecast_days: Number of days to forecast ahead
        
        Returns:
            Tuple of (forecast_df, metrics)
            - forecast_df: DataFrame with columns [date, archived_gb, savings_gb]
            - metrics: Dictionary with model performance metrics
            
        Note: 
            Model returns 2 outputs per input row:
            - archived_gb_next_period: Forecasted archived GB
            - savings_gb_next_period: Forecasted savings in GB
        """
        try:
            # Call endpoint
            result = self.call_endpoint(historical_df)
            
            # Azure ML endpoint returns list of predictions
            # Each prediction is [archived_gb, savings_gb]
            predictions = result if isinstance(result, list) else result.get('predictions', [])
            
            if not predictions:
                raise ValueError("No predictions returned from endpoint")
            
            # Extract archived_gb and savings_gb
            archived_gb_values = []
            savings_gb_values = []
            
            for pred in predictions:
                if isinstance(pred, (list, tuple)) and len(pred) >= 2:
                    archived_gb_values.append(pred[0])
                    savings_gb_values.append(pred[1])
                elif isinstance(pred, dict):
                    archived_gb_values.append(pred.get('archived_gb', 0))
                    savings_gb_values.append(pred.get('savings_gb', 0))
            
            # Generate forecast dates starting from last historical date
            last_historical_date = pd.to_datetime(historical_df['date'].max())
            forecast_dates = pd.date_range(
                start=last_historical_date + timedelta(days=1),
                periods=forecast_days,
                freq='D'
            )
            
            # Build forecast DataFrame
            forecast_df = pd.DataFrame({
                'date': forecast_dates,
                'archived_gb': archived_gb_values[:forecast_days] if archived_gb_values else [np.nan] * forecast_days,
                'savings_gb': savings_gb_values[:forecast_days] if savings_gb_values else [np.nan] * forecast_days,
            })
            
            # Simple metrics based on predictions
            metrics = {
                'model_name': 'smartarchive-archive-forecast',
                'endpoint_url': self.endpoint_url,
                'last_updated': datetime.now().isoformat(),
                'historical_records': len(historical_df),
                'forecast_records': len(forecast_df),
                'avg_archived_gb': float(np.mean(archived_gb_values)) if archived_gb_values else 0,
                'avg_savings_gb': float(np.mean(savings_gb_values)) if savings_gb_values else 0,
            }
            
            return forecast_df, metrics
            
        except Exception as e:
            print(f"Error getting predictions: {str(e)}")
            raise
    
    def get_model_metrics(self, historical_df: pd.DataFrame) -> Dict:
        """
        Extract model metrics from endpoint response
        
        Args:
            historical_df: Historical data
        
        Returns:
            Dictionary with model performance metrics
        """
        try:
            result = self.call_endpoint(historical_df)
            metrics = result.get('metrics', {})
            
            return {
                'r2_score': metrics.get('r2', 0.0),
                'rmse': metrics.get('rmse', 0.0),
                'mae': metrics.get('mae', 0.0),
                'mape': metrics.get('mape', 0.0),
                'model_name': 'smartarchive-archive-forecast',
                'endpoint_url': self.endpoint_url,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error getting metrics: {str(e)}")
            return {}


def get_predictions_from_azure(
    historical_df: pd.DataFrame,
    forecast_days: int = 90
) -> Tuple[pd.DataFrame, Dict]:
    """
    Convenience function to get predictions from Azure ML endpoint
    
    Args:
        historical_df: Historical archive data
        forecast_days: Days to forecast
    
    Returns:
        Tuple of (forecast_df, metrics)
    
    Usage:
        # In your Streamlit app, replace:
        # forecast_df = get_mock_prediction()
        # 
        # With:
        # forecast_df, metrics = get_predictions_from_azure(historical_df)
    """
    client = AzureMLEndpointClient()
    return client.get_predictions(historical_df, forecast_days)


def get_model_metrics_from_azure(historical_df: pd.DataFrame) -> Dict:
    """
    Get model performance metrics from Azure ML endpoint
    
    Usage:
        metrics = get_model_metrics_from_azure(historical_df)
        print(f"Model R² Score: {metrics['r2_score']}")
    """
    client = AzureMLEndpointClient()
    return client.get_model_metrics(historical_df)


if __name__ == "__main__":
    """
    Test the endpoint connection
    
    Run: python src/ml/azure_endpoint_client.py
    """
    print("Testing Azure ML Endpoint Connection...")
    print("-" * 60)
    
    try:
        client = AzureMLEndpointClient()
        print(f"✅ Endpoint configured: {client.endpoint_url}")
        
        # Create sample historical data with all 9 required features
        print("\n📊 Preparing sample historical data (9 features)...")
        
        # Generate realistic sample data
        np.random.seed(42)
        dates = pd.date_range(start='2025-08-14', periods=30, freq='D')
        
        sample_df = pd.DataFrame({
            'date': dates,
            'total_files': np.random.uniform(100000, 150000, 30),
            'avg_file_size_mb': np.random.uniform(1.0, 1.5, 30),
            'pct_pdf': np.random.uniform(0.40, 0.50, 30),
            'pct_docx': np.random.uniform(0.25, 0.35, 30),
            'pct_xlsx': np.random.uniform(0.10, 0.20, 30),
            'pct_other': np.random.uniform(0.05, 0.15, 30),
            'archive_frequency_per_day': np.random.uniform(200, 400, 30),
        })
        
        print(f"   Columns: {list(sample_df.columns)}")
        print(f"   Rows: {len(sample_df)}")
        print(f"   Date range: {sample_df['date'].min().date()} to {sample_df['date'].max().date()}")
        
        print("\n🚀 Calling endpoint...")
        payload = client.prepare_request_payload(sample_df)
        print(f"   Payload structure: input_data[columns, index, data]")
        print(f"   Features ({len(payload['input_data']['columns'])}): {', '.join(payload['input_data']['columns'])}")
        print(f"   Records: {len(payload['input_data']['data'])}")
        
        result = client.call_endpoint(sample_df)
        
        print(f"\n✅ Response received!")
        print(f"   Result type: {type(result)}")
        if isinstance(result, list):
            print(f"   Predictions count: {len(result)}")
            if result:
                print(f"   Sample prediction: archived_gb={result[0][0]:.2f}, savings_gb={result[0][1]:.2f}")
        
        # Get full forecast
        forecast_df, metrics = client.get_predictions(sample_df, forecast_days=30)
        print(f"\n📈 Forecast generated:")
        print(f"   Rows: {len(forecast_df)}")
        print(f"   Columns: {list(forecast_df.columns)}")
        print(f"   Avg archived_gb: {metrics['avg_archived_gb']:.2f}")
        print(f"   Avg savings_gb: {metrics['avg_savings_gb']:.2f}")
        print(f"\n   First 5 rows:")
        print(forecast_df.head())
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check .env file has MLFLOW_ENDPOINT and MLFLOW_API_KEY")
        print("2. Verify endpoint is deployed in Azure ML Studio")
        print("3. Check endpoint deployment status is 'Succeeded'")
        print("4. Verify API key is correct and not expired")
        print("5. Ensure payload format matches endpoint input schema")
        import traceback
        traceback.print_exc()

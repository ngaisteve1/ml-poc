"""
Mock data generation for SmartArchive Archive Forecast UI

Provides realistic mock data for development and testing without real data.
Replace with real data sources when available.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_mock_historical_data(months=12):
    """
    Generate mock historical archive data with all 9 features required by Azure ML model
    
    Args:
        months: Number of months of historical data to generate
    
    Returns:
        DataFrame with columns:
        - date
        - total_files
        - avg_file_size_mb
        - pct_pdf (percentage of PDF files)
        - pct_docx (percentage of DOCX files)
        - pct_xlsx (percentage of XLSX files)
        - pct_other (percentage of other file types)
        - archive_frequency_per_day
        - archived_gb (calculated from total_files * avg_file_size_mb)
    """
    np.random.seed(42)  # For reproducibility
    dates = pd.date_range(end=datetime.now(), periods=months * 30, freq='D')
    
    # Generate realistic archive metrics
    total_files = np.random.uniform(100000, 150000, len(dates))
    avg_file_size_mb = np.random.uniform(1.0, 1.5, len(dates))
    
    # File type percentages (must sum to 1.0)
    pct_pdf = np.random.uniform(0.40, 0.50, len(dates))
    pct_docx = np.random.uniform(0.25, 0.35, len(dates))
    pct_xlsx = np.random.uniform(0.10, 0.20, len(dates))
    pct_other = 1.0 - pct_pdf - pct_docx - pct_xlsx
    
    # Archive frequency per day
    archive_frequency_per_day = np.random.uniform(200, 400, len(dates))
    
    # Calculate archived_gb
    archived_gb = (total_files * avg_file_size_mb) / 1024
    
    df = pd.DataFrame({
        'date': dates,
        'total_files': total_files,
        'avg_file_size_mb': avg_file_size_mb,
        'pct_pdf': pct_pdf,
        'pct_docx': pct_docx,
        'pct_xlsx': pct_xlsx,
        'pct_other': pct_other,
        'archive_frequency_per_day': archive_frequency_per_day,
        'archived_gb': archived_gb,
    })
    
    return df


def get_mock_prediction(days=90):
    """
    Generate mock prediction data
    
    Args:
        days: Number of days to predict ahead
    
    Returns:
        DataFrame with columns: date, archived_gb, savings_gb, confidence_upper, confidence_lower
    """
    # Start from last historical date
    last_historical = datetime.now()
    dates = pd.date_range(start=last_historical, periods=days, freq='D')
    
    # Baseline from last historical value
    base_size = 556  # Approximate current size from historical
    
    archived_gb = []
    savings_gb = []
    confidence_upper = []
    confidence_lower = []
    
    for i, date in enumerate(dates):
        # Linear growth trend
        predicted = base_size + (i * 0.6)  # ~0.6 GB daily growth
        
        # Add uncertainty that increases over time
        uncertainty = 5 + (i * 0.1)  # Growing uncertainty
        
        archived_gb.append(predicted)
        
        # Savings from archiving old data
        savings_gb.append(15 + i * 0.1)  # Increasing savings over time
        
        confidence_upper.append(uncertainty)
        confidence_lower.append(uncertainty * 0.8)
    
    df = pd.DataFrame({
        'date': dates,
        'archived_gb': archived_gb,
        'savings_gb': savings_gb,
        'confidence_upper': confidence_upper,
        'confidence_lower': confidence_lower
    })
    
    return df


def get_mock_metrics():
    """
    Generate mock performance metrics matching Azure ML endpoint output
    
    Returns:
        Dictionary with performance metrics
    """
    return {
        'model_name': 'smartarchive-archive-forecast',
        'endpoint_url': 'https://mlflow-workspace-qzgku.southeastasia.inference.ml.azure.com/score',
        'last_updated': datetime.now().isoformat(),
        'historical_records': 360,
        'forecast_records': 90,
        'avg_archived_gb': 255.52,
        'avg_savings_gb': 132.40,
        
        # Legacy metrics for backwards compatibility
        'current_size': 256.0,
        'current_size_delta': 2.4,
        'predicted_30d': 274.2,
        'predicted_30d_delta': 17.9,
        'potential_savings': 487.5,
        'savings_percent': 46.7,
        'model_accuracy': 87.5,
        'r2_score': 0.875,
        'rmse': 12.34,
        'mae': 8.92,
        'mape': 5.2,
    }


def get_mock_scenario_result(archive_frequency, avg_file_size, retention_days):
    """
    Calculate scenario simulation results
    
    Args:
        archive_frequency: Files per day
        avg_file_size: Average file size in MB
        retention_days: Retention period in days
    
    Returns:
        Dictionary with scenario results
    """
    monthly_growth = (archive_frequency * avg_file_size * 30) / 1024
    total_size = (archive_frequency * avg_file_size * retention_days) / 1024
    
    return {
        'projected_archive_size': total_size,
        'monthly_growth': monthly_growth,
        'yearly_projection': total_size * 4,
        'daily_growth': (archive_frequency * avg_file_size) / 1024,
    }

"""
Mock data generation for SmartArchive Archive Forecast UI

Provides realistic mock data based on SmartArchive SQL data extraction queries.
This data simulates outputs from Query 9 & 10 in 02-data-extraction.sql.

Source Queries:
- Query 1: Monthly Archive Volume Trends (files_archived_count, volume_gb)
- Query 2: File Type Distribution (file_type percentages)
- Query 4: Archive Job Execution History (archive_frequency patterns)
- Query 5: Tenant-Level Archive Performance (aggregate metrics)
- Query 9: Consolidated Training Dataset (all features combined)
- Query 10: Export for CSV - Simplified Training Dataset (direct ML features)

This mock data generation replaces actual database calls for development/testing.
In production, replace with real database queries.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# =====================================================================
# Mock data based on actual SQL query results
# Source: 02-data-extraction.sql Queries 1, 2, 5, 9, 10
# =====================================================================

# Sample data representing actual archive patterns from Query 10
# "Export for CSV - Simplified Training Dataset"
MONTHLY_ARCHIVE_DATA = {
    'period': [
        '2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01', '2024-05-01', '2024-06-01',
        '2024-07-01', '2024-08-01', '2024-09-01', '2024-10-01', '2024-11-01', '2024-12-01'
    ],
    'files_archived': [145000, 152000, 148000, 156000, 162000, 158000,
                       164000, 170000, 168000, 175000, 180000, 182000],
    'volume_gb': [185.2, 194.6, 189.3, 199.8, 207.4, 202.1,
                  209.7, 217.3, 214.8, 223.5, 230.1, 232.8],
    'storage_saved_gb': [89.3, 95.2, 91.8, 97.4, 101.2, 98.7,
                         102.3, 106.1, 104.6, 109.2, 112.4, 113.6],
    'active_tenants': [12, 13, 12, 14, 15, 14, 16, 17, 16, 18, 19, 20],
    'active_sites': [45, 48, 47, 51, 54, 52, 57, 60, 58, 63, 66, 68],
    'avg_file_size_bytes': [1285000, 1281000, 1278000, 1283000, 1279000, 1276000,
                            1282000, 1280000, 1277000, 1281000, 1279000, 1278000],
    'file_type_pdf': [58400, 61120, 59520, 62400, 64800, 63200, 65600, 68000, 67200, 70000, 72000, 72800],
    'file_type_word': [43500, 45600, 44400, 46800, 48600, 47400, 49200, 51000, 50400, 52500, 54000, 54600],
    'file_type_excel': [24150, 25920, 25200, 26520, 27540, 26940, 27960, 28900, 28560, 29750, 30600, 31010],
    'file_type_image': [16200, 17040, 16560, 17280, 18180, 17640, 18960, 19800, 19440, 20750, 21600, 22320],
    'files_with_errors': [1450, 1520, 1480, 1560, 1620, 1580, 1640, 1700, 1680, 1750, 1800, 1820],
    'error_rate_percent': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
}

# Sample file type distribution from Query 2
# "File Type Distribution and Archive Patterns"
FILE_TYPE_STATS = {
    'PDF': {'pct': 0.452, 'description': 'PDF Documents'},
    'Word': {'pct': 0.300, 'description': 'Word Documents (DOCX/DOC)'},
    'Excel': {'pct': 0.165, 'description': 'Excel Spreadsheets (XLSX/XLS)'},
    'Image': {'pct': 0.083, 'description': 'Image Files (JPG/PNG/GIF)'}
}

# Sample tenant-level performance from Query 5
# "Tenant-Level Archive Performance"
TENANT_PERFORMANCE = {
    'tenant_count': 20,
    'avg_files_per_tenant': 9000,
    'avg_volume_per_tenant': 11.65,  # GB
    'avg_storage_saved_per_tenant': 5.68  # GB
}


def get_mock_historical_data(months=12):
    """
    Generate mock historical archive data with 13 features from training dataset.
    
    This data is based on actual SmartArchive SQL query results:
    - Query 10: "Export for CSV - Simplified Training Dataset"
    - Query 1: "Monthly Archive Volume and Trends"
    - Query 2: "File Type Distribution and Archive Patterns"
    - Query 5: "Tenant-Level Archive Performance"
    
    The 13 features in training_data.csv:
    1. period - Date (YYYY-MM-01)
    2. files_archived - Number of files archived monthly
    3. volume_gb - Total archive volume in GB
    4. avg_file_size_mb - Average file size
    5. largest_file_mb - Largest file size
    6. pct_pdf - Percentage of PDF files
    7. pct_docx - Percentage of Word documents
    8. pct_xlsx - Percentage of Excel spreadsheets
    9. archive_frequency_per_day - Files archived per day
    10. storage_saved_gb - Storage freed from deletions
    11. deleted_files_count - Number of deleted files
    12. tenant_count - Number of active tenants
    13. site_count - Number of active sites
    
    Args:
        months: Number of months of historical data to generate (default 12)
    
    Returns:
        DataFrame with 13 feature columns matching training_data.csv structure
    """
    np.random.seed(42)  # For reproducibility
    
    # Generate monthly dates
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=months, freq='MS')
    
    # Use actual data from Query 10 if available, otherwise generate synthetic data
    # based on realistic patterns from the SmartArchive database
    
    if months <= len(MONTHLY_ARCHIVE_DATA['period']):
        # Use actual mock data from Query 10
        actual_df = pd.DataFrame(MONTHLY_ARCHIVE_DATA)
        actual_df['period'] = pd.to_datetime(actual_df['period'])
        
        # Filter to requested months
        latest_months = actual_df.tail(months).copy()
        latest_months['date'] = latest_months['period']
        
        # Calculate required features from Query 10 results
        df = pd.DataFrame({
            'date': pd.to_datetime(latest_months['period']),
            'total_files': latest_months['files_archived'].values,
            'avg_file_size_mb': (latest_months['volume_gb'].values * 1024) / latest_months['files_archived'].values,
            'pct_pdf': np.full(len(latest_months), FILE_TYPE_STATS['PDF']['pct']),
            'pct_docx': np.full(len(latest_months), FILE_TYPE_STATS['Word']['pct']),
            'pct_xlsx': np.full(len(latest_months), FILE_TYPE_STATS['Excel']['pct']),
            'pct_other': np.full(len(latest_months), FILE_TYPE_STATS['Image']['pct']),
            'archive_frequency_per_day': latest_months['files_archived'].values / 30,
            'archived_gb': latest_months['volume_gb'].values,
            'storage_saved_gb': latest_months['storage_saved_gb'].values,
        })
    else:
        # Generate synthetic data following observed patterns from actual data
        # Base trend from Query 1 (monthly volume increasing)
        base_files = 145000
        base_volume = 185.2
        
        # Add growth trend (~2.5% monthly growth based on actual data)
        growth_rate = 0.025
        
        total_files_list = []
        volume_list = []
        storage_saved_list = []
        
        for i in range(months):
            # Linear growth with some variation
            files = base_files * ((1 + growth_rate) ** i)
            # Add monthly variation (±5%)
            files *= (0.95 + np.random.uniform(0, 0.1))
            total_files_list.append(files)
            
            volume = base_volume * ((1 + growth_rate) ** i)
            volume *= (0.95 + np.random.uniform(0, 0.1))
            volume_list.append(volume)
            
            # Storage savings is typically 48% of archived volume (from Query 3)
            storage_saved_list.append(volume * 0.48)
        
        # Calculate average file size from Query 1 data
        avg_file_sizes = (np.array(volume_list) * 1024) / np.array(total_files_list)
        
        df = pd.DataFrame({
            'date': dates,
            'total_files': total_files_list,
            'avg_file_size_mb': avg_file_sizes,
            'pct_pdf': np.full(months, FILE_TYPE_STATS['PDF']['pct']),
            'pct_docx': np.full(months, FILE_TYPE_STATS['Word']['pct']),
            'pct_xlsx': np.full(months, FILE_TYPE_STATS['Excel']['pct']),
            'pct_other': np.full(months, FILE_TYPE_STATS['Image']['pct']),
            'archive_frequency_per_day': np.array(total_files_list) / 30,
            'archived_gb': volume_list,
            'storage_saved_gb': storage_saved_list,
        })
    
    return df


def get_mock_prediction(days=90):
    """
    Generate mock prediction data based on actual SmartArchive patterns.
    
    This data simulates Azure ML endpoint predictions for future archive volume.
    Based on Query 1 and Query 3 trends from 02-data-extraction.sql:
    - Query 1: Monthly Archive Volume growth trending at ~2.5% per month
    - Query 3: Storage Savings trending at ~48% of archived volume
    
    Returns:
        DataFrame with columns:
        - date: Prediction date
        - archived_gb: Forecasted archived volume in GB
        - savings_gb: Forecasted storage savings in GB
        - confidence_upper: Upper confidence interval
        - confidence_lower: Lower confidence interval
    
    Example output structure (matching Query 10 projections):
    ```
    Period              archived_gb  savings_gb
    2024-12-01          232.8        113.6
    2024-12-02          233.4        112.4
    2024-12-03          234.1        112.8
    ```
    """
    # Start from last known historical value
    last_historical_date = datetime.now()
    last_archived_gb = MONTHLY_ARCHIVE_DATA['volume_gb'][-1]  # Latest from Query 10
    last_savings_gb = MONTHLY_ARCHIVE_DATA['storage_saved_gb'][-1]
    
    # Generate forecast dates
    forecast_dates = pd.date_range(start=last_historical_date, periods=days, freq='D')
    
    archived_gb_values = []
    savings_gb_values = []
    confidence_upper = []
    confidence_lower = []
    
    # Simulate continued growth based on Query 1 trend (~2.5% monthly = ~0.08% daily)
    daily_growth_rate = 0.0008
    
    for i, date in enumerate(forecast_dates):
        # Project archive growth with daily compounding
        predicted_gb = last_archived_gb * (1 + daily_growth_rate) ** i
        
        # Savings remain at historical ratio (~48%)
        predicted_savings = predicted_gb * 0.48
        
        archived_gb_values.append(predicted_gb)
        savings_gb_values.append(predicted_savings)
        
        # Confidence interval grows with forecast horizon
        # (typical RMSE from model is ~12.34 GB, growing over time)
        uncertainty = 12.34 * np.sqrt(1 + (i / 30))
        confidence_upper.append(uncertainty)
        confidence_lower.append(uncertainty * 0.8)
    
    df_predicted = pd.DataFrame({
        'date': forecast_dates,
        'archived_gb': archived_gb_values,
        'savings_gb': savings_gb_values,
        'confidence_upper': confidence_upper,
        'confidence_lower': confidence_lower
    })
    
    return df_predicted


def get_mock_metrics():
    """
    Generate mock model performance metrics.
    
    Based on actual SmartArchive model performance trained on Query 9 data:
    - "Consolidated Training Dataset" with all archive metrics
    - Model type: Random Forest + MultiOutput Regressor
    - Features: 9 features as required by Azure ML endpoint
    - Training data: 12 months historical from Query 10
    
    Returns:
        Dictionary with performance and configuration metrics
        matching Azure ML endpoint output format
    """
    # Calculate average metrics from historical data
    df_historical = MONTHLY_ARCHIVE_DATA
    avg_archived_gb = np.mean(df_historical['volume_gb'])
    avg_savings_gb = np.mean(df_historical['storage_saved_gb'])
    avg_error_rate = np.mean(df_historical['error_rate_percent'])
    
    return {
        # Model Information (from Training)
        'model_name': 'smartarchive-archive-forecast',
        'model_version': 'v1.2',
        'model_type': 'RandomForest + MultiOutput',
        'endpoint_url': 'https://mlflow-workspace-qzgku.southeastasia.inference.ml.azure.com/score',
        'last_updated': datetime.now().isoformat(),
        
        # Dataset Information (from Query 9/10)
        'historical_records': len(df_historical['period']),
        'forecast_records': 90,
        'training_months': 12,
        'features_count': 9,
        
        # Archive Metrics (from Query 5: Tenant-Level Performance)
        'avg_archived_gb': avg_archived_gb,
        'avg_savings_gb': avg_savings_gb,
        'total_active_tenants': int(np.mean(df_historical['active_tenants'])),
        'total_active_sites': int(np.mean(df_historical['active_sites'])),
        
        # Azure ML Model Accuracy Metrics
        # (Based on typical Random Forest performance on archive data)
        'r2_score': 0.892,              # R² score: explains 89.2% of variance
        'rmse': 12.34,                  # Root Mean Squared Error in GB
        'mae': 8.92,                    # Mean Absolute Error in GB
        'mape': 5.2,                    # Mean Absolute Percentage Error
        'model_accuracy': 87.5,         # Overall accuracy percentage
        
        # Data Quality Metrics (from Query 7: Archive State Distribution)
        'error_rate_percent': avg_error_rate,
        'data_quality_score': 100 - avg_error_rate,
        
        # Backward compatibility - legacy metric names
        'current_size': avg_archived_gb,
        'current_size_delta': 2.4,
        'predicted_30d': avg_archived_gb + 20,
        'predicted_30d_delta': 20,
        'potential_savings': avg_archived_gb * 0.48,
        'savings_percent': 46.7,
    }


def get_mock_scenario_result(archive_frequency, avg_file_size, retention_days):
    """
    Calculate scenario simulation results based on Query parameters.
    
    This simulates the impact of changing archive parameters, based on:
    - Query 4: Archive Job Execution History (job frequency patterns)
    - Query 6: Weekly Archive Trend Data (volume calculations)
    
    Args:
        archive_frequency: Files per day (from Query 4)
        avg_file_size: Average file size in MB (from Query 1)
        retention_days: Retention period in days (from Query 6)
    
    Returns:
        Dictionary with scenario impact projections
    """
    # Calculate based on archive frequency and file size
    daily_volume_mb = archive_frequency * avg_file_size
    monthly_growth = (daily_volume_mb * 30) / 1024  # Convert to GB
    total_size = (daily_volume_mb * retention_days) / 1024
    
    return {
        'projected_archive_size': total_size,
        'monthly_growth': monthly_growth,
        'yearly_projection': total_size * 4,
        'daily_growth': daily_volume_mb / 1024,
        'potential_savings': total_size * 0.48,  # ~48% savings ratio from Query 3
    }


# =====================================================================
# QUERIES 1-9 Mock Data for Exploration & Feature Engineering
# =====================================================================

def get_query1_monthly_trends():
    """
    Query 1: Monthly Archive Volume and Trends
    
    Aggregates archived files by month to show archive volume trends.
    Used for training regression model on archive volume.
    
    Returns:
        DataFrame with monthly archive statistics
    """
    df = pd.DataFrame(MONTHLY_ARCHIVE_DATA)
    df['period'] = pd.to_datetime(df['period'])
    
    # Calculate additional stats from Query 1
    df['avg_file_size_mb'] = (df['volume_gb'] * 1024) / df['files_archived']
    df['avg_file_size_bytes'] = df['files_archived'] * 1000000  # Normalized
    
    return df[['period', 'files_archived', 'volume_gb', 'avg_file_size_mb', 'active_tenants', 'active_sites']]


def get_query2_file_type_distribution():
    """
    Query 2: File Type Distribution and Archive Patterns
    
    Shows file extension trends and archive frequency by type.
    Used for feature engineering on file types.
    
    Returns:
        DataFrame with file type statistics
    """
    return pd.DataFrame({
        'FileType': list(FILE_TYPE_STATS.keys()),
        'Percentage': [FILE_TYPE_STATS[ft]['pct'] * 100 for ft in FILE_TYPE_STATS.keys()],
        'Description': [FILE_TYPE_STATS[ft]['description'] for ft in FILE_TYPE_STATS.keys()],
        'FilesCount': [int(FILE_TYPE_STATS[ft]['pct'] * 150000) for ft in FILE_TYPE_STATS.keys()],
        'TotalSizeGB': [int(FILE_TYPE_STATS[ft]['pct'] * 200) for ft in FILE_TYPE_STATS.keys()],
    })


def get_query3_storage_saved():
    """
    Query 3: Storage Space Saved (Deleted Files)
    
    Shows files deleted after archiving = storage saved.
    Used for calculating storage savings metric.
    
    Returns:
        DataFrame with monthly storage savings
    """
    df = pd.DataFrame(MONTHLY_ARCHIVE_DATA)
    df['period'] = pd.to_datetime(df['period'])
    
    return df[['period', 'storage_saved_gb']].rename(columns={'period': 'month'})


def get_query4_job_execution():
    """
    Query 4: Archive Job Execution History
    
    Shows archive job execution patterns and frequency.
    Used for understanding archive scheduling and recurrence.
    
    Returns:
        DataFrame with job execution metrics
    """
    jobs_data = {
        'JobId': [1, 2, 3, 4, 5],
        'TenantId': ['tenant_001', 'tenant_002', 'tenant_003', 'tenant_001', 'tenant_002'],
        'JobType': ['Incremental', 'Full', 'Incremental', 'Full', 'Incremental'],
        'TotalFilesArchived': [45000, 52000, 38000, 48000, 41000],
        'AvgDaysBetweenArchives': [7, 30, 5, 14, 10]
    }
    return pd.DataFrame(jobs_data)


def get_query5_tenant_performance():
    """
    Query 5: Tenant-Level Archive Performance
    
    Aggregated metrics by tenant for prediction.
    Used for tenant-level forecasting features.
    
    Returns:
        DataFrame with tenant-level statistics
    """
    tenants = [f'tenant_{str(i).zfill(3)}' for i in range(1, 21)]
    np.random.seed(42)
    
    tenant_data = {
        'TenantId': tenants,
        'TotalFilesArchived': np.random.randint(3000, 15000, 20),
        'UniqueSitesArchived': np.random.randint(2, 8, 20),
        'TotalArchiveVolumeGB': np.random.uniform(15, 45, 20),
        'ArchiveActivitySpanDays': np.random.randint(30, 365, 20),
        'StorageSavedGB': np.random.uniform(7, 22, 20),
        'DeletedPercentage': np.random.uniform(40, 60, 20),
    }
    return pd.DataFrame(tenant_data)


def get_query6_weekly_trends():
    """
    Query 6: Weekly Archive Trend Data
    
    Weekly aggregation for more granular time-series analysis.
    Used for time-series forecasting model.
    
    Returns:
        DataFrame with weekly archive data
    """
    weeks = []
    for i in range(52):
        week_start = datetime.now() - timedelta(days=365-i*7)
        weeks.append({
            'Week': week_start.isocalendar()[1],
            'Date': week_start,
            'FilesArchivedCount': np.random.randint(15000, 25000),
            'VolumeGBArchived': np.random.uniform(20, 35),
            'ActiveTenants': np.random.randint(5, 15),
            'ActiveSites': np.random.randint(20, 50),
        })
    return pd.DataFrame(weeks)


def get_query7_archive_state():
    """
    Query 7: Archive State Distribution
    
    Shows file states and potential data quality issues.
    Used for data quality and state transition analysis.
    
    Returns:
        DataFrame with archive state distribution
    """
    states = {
        'FileState': ['Pending', 'Archiving', 'Archived', 'Failed', 'Restored'],
        'FileCount': [5000, 2000, 574000, 1500, 3500],
        'TotalSizeGB': [6.4, 2.6, 735.1, 1.9, 4.5],
        'PercentOfTotal': [0.8, 0.3, 96.6, 0.2, 0.5],
        'FilesWithErrors': [4500, 1800, 1150, 1500, 100],
    }
    return pd.DataFrame(states)


def get_query8_size_distribution():
    """
    Query 8: Archive Size Distribution (Quantiles)
    
    Shows file size distribution patterns.
    Used for understanding archive patterns and outliers.
    
    Returns:
        DataFrame with percentile statistics
    """
    return pd.DataFrame({
        'Percentile': ['Q1 (25%)', 'Q2 (Median)', 'Q3 (75%)', 'P95', 'P99'],
        'FileSizeBytes': [524288, 1048576, 2097152, 5242880, 10485760],
        'FileSizeMB': [0.5, 1.0, 2.0, 5.0, 10.0],
        'Description': [
            'Small files (docs, emails)',
            'Typical file size',
            'Large files (videos, archives)',
            '95th percentile - Very large',
            '99th percentile - Outliers'
        ]
    })


def get_query9_consolidated_dataset():
    """
    Query 9: Consolidated Training Dataset
    
    Combines monthly archive volume with all relevant features.
    Used for direct ML model training.
    
    Returns:
        DataFrame with all features for training
    """
    df = pd.DataFrame(MONTHLY_ARCHIVE_DATA)
    df['period'] = pd.to_datetime(df['period'])
    
    # Rename for clarity
    df = df.rename(columns={
        'period': 'MonthStart',
        'files_archived': 'FilesArchivedCount',
        'volume_gb': 'VolumeGBArchived',
        'storage_saved_gb': 'StorageSavedGB',
        'active_tenants': 'ActiveTenants',
        'active_sites': 'ActiveSites',
        'file_type_pdf': 'PDFCount',
        'file_type_word': 'WordCount',
        'file_type_excel': 'ExcelCount',
        'file_type_image': 'ImageCount',
        'files_with_errors': 'FilesWithErrors',
    })
    
    # Calculate percentages
    total = df['FilesArchivedCount'].sum()
    df['PDFPercent'] = (df['PDFCount'] / df['FilesArchivedCount'] * 100).round(2)
    df['WordPercent'] = (df['WordCount'] / df['FilesArchivedCount'] * 100).round(2)
    df['ExcelPercent'] = (df['ExcelCount'] / df['FilesArchivedCount'] * 100).round(2)
    
    return df

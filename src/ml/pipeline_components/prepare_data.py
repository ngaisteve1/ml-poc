"""
SmartArchive Data Preparation Component
Prepares archive data from CSV, database, or API for model training.
Generates synthetic SmartArchive data if real data is not available.
"""
import os
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta

def generate_synthetic_archive_data(num_records: int = 1000) -> pd.DataFrame:
    """Generate synthetic SmartArchive data for POC/testing"""
    np.random.seed(42)
    
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(num_records)]
    
    data = {
        'date': dates,
        'month': [d.strftime("%Y-%m-01") for d in dates],
        'tenant_id': np.random.choice(['tenant_001', 'tenant_002', 'tenant_003'], num_records),
        'total_files': np.random.randint(10000, 100000, num_records),
        'avg_file_size_mb': np.random.uniform(0.5, 5.0, num_records),
        'pct_pdf': np.random.uniform(0.2, 0.6, num_records),
        'pct_docx': np.random.uniform(0.1, 0.4, num_records),
        'pct_xlsx': np.random.uniform(0.05, 0.3, num_records),
        'archive_frequency_per_day': np.random.uniform(10, 200, num_records),
        'files_archived': np.random.randint(100, 5000, num_records),
        'archived_gb': np.random.uniform(50, 500, num_records),
        'savings_gb': np.random.uniform(25, 250, num_records),
        'site_count': np.random.randint(1, 50, num_records),
    }
    
    df = pd.DataFrame(data)
    
    # Add percentage for 'other' file types
    df['pct_other'] = 1.0 - (df['pct_pdf'] + df['pct_docx'] + df['pct_xlsx'])
    df['pct_other'] = df['pct_other'].clip(lower=0.0)
    
    return df

def load_archive_data(input_source: str = None) -> pd.DataFrame:
    """
    Load SmartArchive data from various sources:
    - CSV file
    - Database query
    - API endpoint
    - Synthetic data (fallback)
    """
    
    if input_source and os.path.exists(input_source):
        print(f"Loading SmartArchive data from CSV: {input_source}")
        df = pd.read_csv(input_source)
    else:
        print("No input data source specified or found. Generating synthetic SmartArchive data...")
        df = generate_synthetic_archive_data(num_records=1000)
    
    return df

def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare and validate SmartArchive data for model training.
    Handles:
    - Missing values
    - Data type conversion
    - Feature engineering
    """
    
    print(f"Preparing data. Initial shape: {df.shape}")
    
    # Ensure required columns exist
    required_columns = [
        'total_files', 'avg_file_size_mb', 'pct_pdf', 'pct_docx', 'pct_xlsx',
        'archive_frequency_per_day', 'files_archived', 'archived_gb', 'savings_gb'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"Warning: Missing columns {missing_cols}. They will be filled with random data.")
        for col in missing_cols:
            df[col] = np.random.uniform(0.1, 100, len(df))
    
    # Drop rows with missing critical values
    df = df.dropna(subset=['archived_gb', 'savings_gb'])
    
    # Ensure numeric types
    numeric_cols = required_columns
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop any remaining NaN rows
    df = df.dropna()
    
    print(f"Data prepared. Final shape: {df.shape}")
    
    if df.shape[0] == 0:
        print("ERROR: No valid data after preparation.")
        raise ValueError("Data preparation resulted in empty dataset")
    
    return df

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Prepare SmartArchive data for model training"
    )
    parser.add_argument(
        "--output_data",
        type=str,
        required=True,
        help="Output directory for prepared data"
    )
    parser.add_argument(
        "--input_data",
        type=str,
        default=None,
        help="Optional input CSV file for real SmartArchive data"
    )
    args = parser.parse_args()
    
    # Load data
    print("=" * 60)
    print("SmartArchive Data Preparation Component")
    print("=" * 60)
    
    df = load_archive_data(args.input_data)
    print(f"Data loaded. Shape: {df.shape}")
    
    # Prepare data
    df = prepare_data(df)
    
    # Ensure output directory exists
    os.makedirs(args.output_data, exist_ok=True)
    
    # Save prepared data
    output_path = os.path.join(args.output_data, "archive-data.csv")
    df.to_csv(output_path, index=False)
    print(f"✅ Prepared data saved to {output_path}")
    
    # Print summary
    print("\nData Summary:")
    print(f"  Total records: {len(df)}")
    print(f"  Average archived GB: {df['archived_gb'].mean():.2f}")
    print(f"  Average savings GB: {df['savings_gb'].mean():.2f}")
    print(f"  Columns: {', '.join(df.columns.tolist())}")

if __name__ == "__main__":
    main()

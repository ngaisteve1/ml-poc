"""
Generate realistic mock data for ML POC testing without touching production DB.

This script creates a CSV file with realistic archive data patterns that mimics
what you would get from Query 10 in the database.

Usage:
    python src/ml/generate_mock_data.py
    python src/ml/generate_mock_data.py --output data/training_data.csv --rows 24
"""

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_mock_data(
    output_path: str = "data/training_data.csv",
    num_rows: int = 24,
    start_date: str = "2023-01-01",
    seed: int = 42
) -> None:
    """
    Generate realistic mock archive data.
    
    Args:
        output_path: Where to save the CSV file
        num_rows: Number of months of data to generate (default 24 = 2 years)
        start_date: Starting month (YYYY-MM-01 format)
        seed: Random seed for reproducibility
    
    The generated data includes:
    - Realistic archive volume trends (growth pattern)
    - Seasonal patterns (peaks mid-year)
    - File type distributions
    - Storage savings calculations
    - Archive frequency variations
    """
    
    random.seed(seed)
    
    # Parse start date
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    # CSV headers matching Query 10 output
    headers = [
        "period",                          # YYYY-MM-01
        "files_archived",                  # Count of files archived
        "volume_gb",                       # Total volume in GB
        "avg_file_size_mb",                # Average file size
        "largest_file_mb",                 # Largest file in period
        "pct_pdf",                         # PDF percentage
        "pct_docx",                        # Word doc percentage
        "pct_xlsx",                        # Excel percentage
        "archive_frequency_per_day",       # Archive jobs per day
        "storage_saved_gb",                # Storage freed (from deletions)
        "deleted_files_count",             # Files deleted after archive
        "tenant_count",                    # Number of tenants
        "site_count"                       # Number of sites
    ]
    
    # Base values (will be varied with trends and randomness)
    base_files = 10_000
    base_volume_gb = 50
    base_frequency = 150
    
    data_rows = []
    
    for month_idx in range(num_rows):
        period = current_date.strftime("%Y-%m-01")
        
        # Simulate growth trend
        growth_factor = 1 + (month_idx * 0.02)  # 2% growth per month
        
        # Seasonal pattern (peak in June-August)
        month = current_date.month
        seasonal_factor = 1.0
        if 6 <= month <= 8:
            seasonal_factor = 1.3  # 30% higher in summer
        elif month in [12, 1]:
            seasonal_factor = 0.7  # 30% lower in winter
        
        # Add random variation (±15%)
        random_variation = random.uniform(0.85, 1.15)
        
        # Calculate values
        files_archived = int(base_files * growth_factor * seasonal_factor * random_variation)
        volume_gb = base_volume_gb * growth_factor * seasonal_factor * random_variation
        avg_file_size_mb = (volume_gb * 1024) / files_archived if files_archived > 0 else 5.0
        largest_file_mb = avg_file_size_mb * random.uniform(3, 8)
        
        # File type distribution (realistic percentages)
        pct_pdf = random.uniform(0.35, 0.45)
        pct_docx = random.uniform(0.25, 0.35)
        pct_xlsx = random.uniform(0.15, 0.25)
        # Remaining is other file types (implicitly 1 - sum)
        
        # Archive frequency (jobs per day)
        archive_frequency = base_frequency * growth_factor * seasonal_factor * random_variation
        
        # Storage savings (typically 40-60% of archived volume)
        savings_factor = random.uniform(0.4, 0.6)
        storage_saved_gb = volume_gb * savings_factor
        
        # Deleted files (typically 70-90% of archived files are deleted within period)
        deletion_rate = random.uniform(0.7, 0.9)
        deleted_files = int(files_archived * deletion_rate)
        
        # Tenant and site counts (vary slightly)
        tenant_count = random.randint(15, 25)
        site_count = random.randint(80, 150)
        
        # Build row
        row = [
            period,
            files_archived,
            round(volume_gb, 2),
            round(avg_file_size_mb, 2),
            round(largest_file_mb, 2),
            round(pct_pdf, 4),
            round(pct_docx, 4),
            round(pct_xlsx, 4),
            round(archive_frequency, 1),
            round(storage_saved_gb, 2),
            deleted_files,
            tenant_count,
            site_count
        ]
        
        data_rows.append(row)
        
        # Move to next month
        current_date += timedelta(days=32)
        current_date = current_date.replace(day=1)
    
    # Write CSV file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data_rows)
    
    print(f"✅ Generated {num_rows} months of mock data")
    print(f"📁 Saved to: {output_file.resolve()}")
    print(f"📊 File size: {output_file.stat().st_size / 1024:.1f} KB")
    
    # Print sample
    print(f"\n📋 Sample data (first 5 rows):")
    print(f"   Period: {data_rows[0][0]} to {data_rows[-1][0]}")
    print(f"   Files archived (avg): {sum(r[1] for r in data_rows) // len(data_rows):,}")
    print(f"   Volume (total): {sum(r[2] for r in data_rows):.1f} GB")
    print(f"   Storage saved (total): {sum(r[9] for r in data_rows):.1f} GB")


def main():
    parser = argparse.ArgumentParser(
        description="Generate realistic mock archive data for ML POC testing"
    )
    parser.add_argument(
        "--output",
        default="data/training_data.csv",
        help="Output CSV file path (default: data/training_data.csv)"
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=24,
        help="Number of months to generate (default: 24 = 2 years)"
    )
    parser.add_argument(
        "--start-date",
        default="2023-01-01",
        help="Start date in YYYY-MM-01 format (default: 2023-01-01)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    
    args = parser.parse_args()
    
    try:
        generate_mock_data(
            output_path=args.output,
            num_rows=args.rows,
            start_date=args.start_date,
            seed=args.seed
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()

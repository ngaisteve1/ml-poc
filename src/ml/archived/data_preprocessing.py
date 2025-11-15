"""
ML POC: Data Loading and Preprocessing Utilities
Purpose: Helper functions to load and prepare extracted SQL data for ML training
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """Load and validate archive data from SQL exports"""
    
    def __init__(self, data_path: str = 'ml-poc/data/training_data.csv'):
        """
        Initialize data loader
        
        Args:
            data_path: Path to CSV file exported from SQL Query 10
        """
        self.data_path = Path(data_path)
        self.df = None
        
    def load(self) -> pd.DataFrame:
        """Load data from CSV"""
        try:
            self.df = pd.read_csv(self.data_path)
            logger.info(f"✓ Loaded {len(self.df)} rows from {self.data_path}")
            logger.info(f"  Columns: {list(self.df.columns)}")
            return self.df
        except FileNotFoundError:
            logger.error(f"✗ File not found: {self.data_path}")
            raise
    
    def validate(self) -> bool:
        """Validate data quality"""
        if self.df is None:
            logger.error("✗ No data loaded. Call load() first.")
            return False
        
        checks = {
            'null_values': self.df.isnull().sum().sum(),
            'duplicate_rows': self.df.duplicated().sum(),
            'negative_volumes': (self.df['volume_gb'] < 0).sum(),
            'negative_file_counts': (self.df['files_archived'] < 0).sum(),
        }
        
        logger.info("Data Quality Checks:")
        for check, count in checks.items():
            status = "✓" if count == 0 else "✗"
            logger.info(f"  {status} {check}: {count}")
        
        return all(v == 0 for v in checks.values())
    
    def summarize(self):
        """Print data summary statistics"""
        if self.df is None:
            logger.error("✗ No data loaded.")
            return
        
        logger.info("\n📊 Data Summary Statistics:")
        logger.info(f"  Period: {self.df['Period'].min()} to {self.df['Period'].max()}")
        logger.info(f"  Total Months: {len(self.df)}")
        logger.info(f"  Archive Volume (GB): {self.df['volume_gb'].sum():.2f}")
        logger.info(f"  Total Files Archived: {self.df['files_archived'].sum()}")
        logger.info(f"  Storage Saved (GB): {self.df['storage_saved_gb'].sum():.2f}")
        logger.info(f"  Average Deletion Rate: {self.df['storage_saved_gb'].sum() / self.df['volume_gb'].sum() * 100:.1f}%")


class DataPreprocessor:
    """Preprocess and engineer features for ML training"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize preprocessor
        
        Args:
            df: DataFrame from DataLoader
        """
        self.df = df.copy()
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.target_column = None
        
    def create_lag_features(self, windows=[1, 3, 12]) -> pd.DataFrame:
        """Create lag features for time-series forecasting"""
        logger.info(f"Creating lag features: {windows}")
        
        for window in windows:
            self.df[f'volume_gb_lag{window}'] = self.df['volume_gb'].shift(window)
            self.df[f'files_archived_lag{window}'] = self.df['files_archived'].shift(window)
        
        # Forward-fill for first few rows
        self.df.fillna(method='bfill', inplace=True)
        
        logger.info(f"✓ Added {len(windows) * 2} lag features")
        return self.df
    
    def create_growth_features(self) -> pd.DataFrame:
        """Create growth rate features"""
        logger.info("Creating growth rate features")
        
        self.df['volume_growth_rate'] = self.df['volume_gb'].pct_change()
        self.df['file_count_growth_rate'] = self.df['files_archived'].pct_change()
        self.df['storage_saved_growth_rate'] = self.df['storage_saved_gb'].pct_change()
        
        # Fill NaN with 0
        self.df.fillna(0, inplace=True)
        
        logger.info("✓ Added 3 growth rate features")
        return self.df
    
    def create_temporal_features(self) -> pd.DataFrame:
        """Create temporal features (seasonality)"""
        logger.info("Creating temporal features")
        
        # Convert Period to datetime if needed
        if self.df['Period'].dtype == 'object':
            self.df['Period'] = pd.to_datetime(self.df['Period'])
        
        self.df['month'] = self.df['Period'].dt.month
        self.df['quarter'] = self.df['Period'].dt.quarter
        self.df['year'] = self.df['Period'].dt.year
        self.df['is_q4'] = self.df['quarter'].isin([4]).astype(int)
        self.df['is_summer'] = self.df['month'].isin([6, 7, 8]).astype(int)
        
        logger.info("✓ Added 5 temporal features")
        return self.df
    
    def create_engagement_features(self) -> pd.DataFrame:
        """Create user engagement features"""
        logger.info("Creating engagement features")
        
        self.df['engagement_score'] = (
            (self.df['active_tenants'] + self.df['active_sites']) / 2
        )
        
        self.df['file_type_diversity'] = (
            self.df['file_type_pdf'] + 
            self.df['file_type_word'] + 
            self.df['file_type_excel'] + 
            self.df['file_type_image']
        ) / self.df['files_archived'].replace(0, 1)
        
        self.df['document_ratio'] = (
            self.df['file_type_word'] + self.df['file_type_excel']
        ) / self.df['files_archived'].replace(0, 1)
        
        logger.info("✓ Added 3 engagement features")
        return self.df
    
    def create_all_features(self) -> pd.DataFrame:
        """Create all feature sets"""
        logger.info("\n🔧 Feature Engineering Pipeline:")
        self.create_lag_features()
        self.create_growth_features()
        self.create_temporal_features()
        self.create_engagement_features()
        
        logger.info(f"✓ Total features created: {len(self.df.columns)}")
        return self.df
    
    def get_features_and_target(
        self, 
        target='volume_gb',
        exclude_columns=['Period']
    ):
        """
        Extract features (X) and target (y) for ML training
        
        Args:
            target: Target column name
            exclude_columns: Columns to exclude from features
            
        Returns:
            (X, y) - Feature matrix and target vector
        """
        self.target_column = target
        
        # Select all numeric columns except target and excluded
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        self.feature_columns = [
            col for col in numeric_cols 
            if col != target and col not in exclude_columns
        ]
        
        X = self.df[self.feature_columns]
        y = self.df[target]
        
        logger.info(f"\n📊 ML Dataset:")
        logger.info(f"  Features (X): {len(self.feature_columns)} features")
        logger.info(f"  Target (y): {target}")
        logger.info(f"  Samples: {len(X)}")
        
        return X, y


class DataSplitter:
    """Split data for training and evaluation"""
    
    @staticmethod
    def time_series_split(X, y, test_size=0.2):
        """
        Time-series aware train-test split
        
        Args:
            X: Features
            y: Target
            test_size: Fraction of data for testing
            
        Returns:
            (X_train, X_test, y_train, y_test)
        """
        split_point = int(len(X) * (1 - test_size))
        
        X_train = X.iloc[:split_point]
        X_test = X.iloc[split_point:]
        y_train = y.iloc[:split_point]
        y_test = y.iloc[split_point:]
        
        logger.info(f"\n🔀 Time-Series Split ({test_size*100}% test):")
        logger.info(f"  Train: {len(X_train)} samples")
        logger.info(f"  Test: {len(X_test)} samples")
        
        return X_train, X_test, y_train, y_test
    
    @staticmethod
    def random_split(X, y, test_size=0.2, random_state=42):
        """
        Random train-test split (if temporal order not critical)
        
        Args:
            X: Features
            y: Target
            test_size: Fraction of data for testing
            random_state: Random seed for reproducibility
            
        Returns:
            (X_train, X_test, y_train, y_test)
        """
        return train_test_split(X, y, test_size=test_size, random_state=random_state)


class FeatureScaler:
    """Scale features for ML training"""
    
    def __init__(self, method='standard'):
        """
        Initialize scaler
        
        Args:
            method: 'standard' (mean=0, std=1) or 'minmax' (0-1)
        """
        self.method = method
        self.scaler = StandardScaler() if method == 'standard' else MinMaxScaler()
    
    def fit_transform(self, X_train, X_test=None):
        """Fit on training data and transform both sets"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
        
        if X_test is not None:
            X_test_scaled = self.scaler.transform(X_test)
            X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
            return X_train_scaled, X_test_scaled
        
        return X_train_scaled


# ============================================================================
# Usage Example
# ============================================================================

def example_workflow():
    """
    Example workflow: Load → Validate → Preprocess → Train
    """
    # 1. Load data
    loader = DataLoader('ml-poc/data/training_data.csv')
    df = loader.load()
    loader.validate()
    loader.summarize()
    
    # 2. Preprocess
    preprocessor = DataPreprocessor(df)
    df_processed = preprocessor.create_all_features()
    
    # 3. Get features and target
    X, y = preprocessor.get_features_and_target(target='volume_gb')
    
    # 4. Split data
    X_train, X_test, y_train, y_test = DataSplitter.time_series_split(X, y, test_size=0.2)
    
    # 5. Scale features
    scaler = FeatureScaler(method='standard')
    X_train_scaled, X_test_scaled = scaler.fit_transform(X_train, X_test)
    
    logger.info("\n✓ Data pipeline complete! Ready for model training.")
    
    return X_train_scaled, X_test_scaled, y_train, y_test


if __name__ == '__main__':
    # Run example workflow
    example_workflow()

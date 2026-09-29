"""
Normalization Module
Reusable scaling logic for AI/ML pipelines.
"""
import pandas as pd
from sklearn.preprocessing import StandardScaler
from typing import List, Tuple, Optional, Any

def fit_scaler(df: pd.DataFrame, columns: List[str]) -> StandardScaler:
    """
    Fits a StandardScaler on the provided DataFrame columns.
    Must ONLY be run on training data.
    """
    scaler = StandardScaler()
    scaler.fit(df[columns])
    return scaler

def transform_with_scaler(df: pd.DataFrame, scaler: StandardScaler, columns: List[str]) -> pd.DataFrame:
    """
    Transforms the provided DataFrame columns using an already fitted scaler.
    """
    df = df.copy()
    df[columns] = scaler.transform(df[columns])
    return df

def normalize_features(
    train_df: pd.DataFrame,
    test_df: Optional[pd.DataFrame] = None,
    columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], StandardScaler]:
    """
    Convenience function to fit on training data and transform both train and test data.
    Returns scaled train df, scaled test df (if provided), and the fitted scaler.
    """
    if columns is None:
        # Default to all numeric columns except target/id columns if None specified
        # Here we just take all numeric columns except timestamp, station_id
        columns = train_df.select_dtypes(include=['number']).columns.tolist()
        
    scaler = fit_scaler(train_df, columns)
    
    scaled_train = transform_with_scaler(train_df, scaler, columns)
    
    scaled_test = None
    if test_df is not None:
        scaled_test = transform_with_scaler(test_df, scaler, columns)
        
    return scaled_train, scaled_test, scaler

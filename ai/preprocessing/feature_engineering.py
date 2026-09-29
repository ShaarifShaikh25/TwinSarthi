"""
Feature Engineering Module
Creates time, lag, rolling, and domain-specific features for ML models.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .clean_data import flatten_telemetry, handle_outliers, handle_missing_values

def create_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates temporal features from the timestamp.
    """
    df = df.copy()
    if "timestamp" in df.columns:
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["day_of_year"] = df["timestamp"].dt.dayofyear
        df["month"] = df["timestamp"].dt.month
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        
        # Cyclic representation for hour (24 hours)
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
        
    return df

def create_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates lag features for time-series forecasting.
    Uses historical data (T-N) without leaking future data.
    """
    df = df.copy()
    lag_cols = [
        "power_consumption_kw",
        "fuel_level_liters",
        "generator_load_percent",
        "temperature_c"
    ]
    lags = [1, 3, 6]
    
    for col in lag_cols:
        if col in df.columns:
            for lag in lags:
                df[f"{col}_lag_{lag}"] = df.groupby("station_id")[col].shift(lag)
                
    return df

def create_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates rolling historical statistics.
    Applies shift(1) before rolling to ensure current target is not leaked.
    """
    df = df.copy()
    roll_cols = [
        "power_consumption_kw",
        "generator_load_percent",
        "fuel_consumption_lph",
        "temperature_c"
    ]
    window = 6
    
    for col in roll_cols:
        if col in df.columns:
            # Shift by 1 first to avoid target leakage, then apply rolling
            shifted = df.groupby("station_id")[col].shift(1)
            df[f"{col}_rolling_mean_{window}"] = shifted.groupby(df["station_id"]).rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
            df[f"{col}_rolling_std_{window}"] = shifted.groupby(df["station_id"]).rolling(window, min_periods=1).std().reset_index(level=0, drop=True)
            
            # Fill NaNs from std calculation (when min_periods=1 yields 1 sample, std is NaN)
            df[f"{col}_rolling_std_{window}"] = df[f"{col}_rolling_std_{window}"].fillna(0.0)
            
    return df

def create_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates explainable operational features based on domain logic.
    """
    df = df.copy()
    
    # Generator Load Fraction
    if "generator_load_percent" in df.columns:
        df["generator_load_fraction"] = df["generator_load_percent"] / 100.0
        
    # HVAC to Power Ratio
    if "hvac_load_kw" in df.columns and "power_consumption_kw" in df.columns:
        # Avoid division by zero
        safe_power = df["power_consumption_kw"].replace(0, np.nan)
        df["hvac_to_power_ratio"] = (df["hvac_load_kw"] / safe_power).fillna(0.0)
        
    # Temperature Deviation from a configured prototype reference (-15C)
    if "temperature_c" in df.columns:
        REFERENCE_TEMP_C = -15.0
        df["temperature_deviation"] = df["temperature_c"] - REFERENCE_TEMP_C
        
    return df

def build_ml_features(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Main pipeline:
    1. Flatten
    2. Handle Outliers (flag / reject impossible)
    3. Handle Missing Values
    4. Time Features
    5. Lag Features
    6. Rolling Features
    7. Domain Features
    
    Returns a clean, ML-ready pandas DataFrame. Does NOT automatically scale.
    """
    if not records:
        return pd.DataFrame()
        
    # 1. Flatten
    df = flatten_telemetry(records)
    
    # 2. Outliers
    df = handle_outliers(df)
    
    # 3. Missing
    df = handle_missing_values(df)
    
    # 4. Time
    df = create_time_features(df)
    
    # 5. Lag
    df = create_lag_features(df)
    
    # 6. Rolling
    df = create_rolling_features(df)
    
    # 7. Domain
    df = create_domain_features(df)
    
    # Do NOT backfill lag/rolling features to prevent future data leakage.
    # Warm-up rows with NaNs should be dropped during ML training.
    
    return df

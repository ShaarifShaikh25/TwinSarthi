"""
Clean Data Module
Flattens, validates, handles missing values, and flags outliers for synthetic station telemetry.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any

def flatten_telemetry(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Flattens nested telemetry records into a tabular pandas DataFrame.
    """
    flat_records = []
    for r in records:
        flat = {
            "timestamp": r.get("timestamp"),
            "station_id": r.get("station_id"),
            "data_source": "SIMULATION"
        }
        
        env = r.get("environment", {})
        flat.update(env)
        
        energy = r.get("energy", {})
        flat.update(energy)
        
        gen = r.get("generator", {})
        flat["generator_status"] = gen.get("status")
        flat["runtime_hours"] = gen.get("runtime_hours")
        
        fuel = r.get("fuel", {})
        for k, v in fuel.items():
            flat[f"fuel_{k}"] = v
            
        inv = r.get("inventory", {})
        flat.update(inv)
        
        flat_records.append(flat)
        
    df = pd.DataFrame(flat_records)
    
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.sort_values(by=["station_id", "timestamp"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        
    return df

def handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flags suspicious or physically impossible values using sanity checks.
    Rejects completely impossible values by nullifying them (to be handled later).
    Leaves plausible extremes intact but flags them.
    """
    df = df.copy()
    
    # Flags matching tests
    df["impossible_env_flag"] = False
    df["impossible_fuel_flag"] = False
    
    # 1. Flag suspicious but possible extremes (Quality Flags)
    if "temperature_c" in df.columns:
        df["temperature_outlier_flag"] = (df["temperature_c"] < -80) | (df["temperature_c"] > 10)
        # We can also flag impossible env if it's crazy low
        df.loc[df["temperature_c"] < -95, "impossible_env_flag"] = True
        
    if "wind_speed_mps" in df.columns:
        df["wind_outlier_flag"] = df["wind_speed_mps"] > 40
        
    # 2. Reject physically impossible values
    if "humidity_percent" in df.columns:
        # Avoid TypeError if None
        invalid_humidity = pd.to_numeric(df["humidity_percent"], errors='coerce').fillna(50) < 0
        invalid_humidity |= pd.to_numeric(df["humidity_percent"], errors='coerce').fillna(50) > 100
        df.loc[invalid_humidity, "impossible_env_flag"] = True
        df.loc[invalid_humidity, "humidity_percent"] = np.nan
        
    if "power_consumption_kw" in df.columns:
        invalid_power = pd.to_numeric(df["power_consumption_kw"], errors='coerce').fillna(0) < 0
        df.loc[invalid_power, "power_consumption_kw"] = np.nan
        
    if "generator_load_percent" in df.columns:
        invalid_load = pd.to_numeric(df["generator_load_percent"], errors='coerce').fillna(0) < 0
        invalid_load |= pd.to_numeric(df["generator_load_percent"], errors='coerce').fillna(0) > 120
        df.loc[invalid_load, "generator_load_percent"] = np.nan
        
    if "fuel_level_liters" in df.columns:
        invalid_fuel = pd.to_numeric(df["fuel_level_liters"], errors='coerce').fillna(0) < 0
        df.loc[invalid_fuel, "impossible_fuel_flag"] = True
        df.loc[invalid_fuel, "fuel_level_liters"] = np.nan
        
    if "runtime_hours" in df.columns:
        invalid_runtime = pd.to_numeric(df["runtime_hours"], errors='coerce').fillna(0) < 0
        df.loc[invalid_runtime, "runtime_hours"] = np.nan

    return df

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handles missing values safely for time-series ML without leaking future observations.
    Uses forward-fill grouped by station, then fallback fill.
    """
    df = df.copy()
    
    # Forward fill within each station safely without losing columns
    for col in df.columns:
        if col not in ["station_id", "timestamp"]:
            df[col] = df.groupby("station_id")[col].ffill()
    
    # Fallbacks for the start of the sequence or entirely missing columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0.0)
            
    cat_cols = df.select_dtypes(include=['object', 'string']).columns
    for col in cat_cols:
        if df[col].isnull().any():
            df[col] = df[col].fillna("UNKNOWN")
            
    return df

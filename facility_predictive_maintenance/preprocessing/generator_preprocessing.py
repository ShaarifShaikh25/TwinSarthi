import pandas as pd
import json
from pathlib import Path
from preprocessing.data_quality import assess_data_quality
from preprocessing.timestamp_processing import normalize_timestamps
from preprocessing.missing_data import handle_missing_data
from preprocessing.outlier_detection import flag_statistical_outliers

def apply_plausibility_limits(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineering sanity checks for generator.
    These are SIMULATION/ENGINEERING ASSUMPTIONS, not official NCPOR limits.
    """
    df_clean = df.copy()
    
    # Invalid RPM
    df_clean.loc[df_clean['rpm'] < 0, 'rpm'] = pd.NA
    # Constrain Load
    df_clean.loc[df_clean['load_pct'] < 0, 'load_pct'] = 0
    df_clean.loc[df_clean['load_pct'] > 110, 'load_pct'] = 110
    
    # Impossible sensor values (e.g. coolant > 200C is physically unlikely without catastrophic instant failure)
    df_clean.loc[df_clean['coolant_temp_c'] > 150, 'coolant_temp_c'] = pd.NA
    df_clean.loc[df_clean['coolant_temp_c'] < -50, 'coolant_temp_c'] = pd.NA
    
    return df_clean

def preprocess_generator_data(csv_path: str, dataset_name: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 1. Data Quality Assessment
    report = assess_data_quality(df, dataset_name)
    print(f"\nData Quality Report for {dataset_name}:")
    print(json.dumps(report, indent=2))
    
    # 2. Timestamp Normalization & Gap Detection
    df = normalize_timestamps(df, expected_freq='1min')
    
    # 3. Plausibility Limits
    df = apply_plausibility_limits(df)
    
    # 4. Outlier Flagging (do not drop them)
    outlier_cols = ['exhaust_temp_c', 'vibration_mm_s', 'coolant_temp_c']
    df = flag_statistical_outliers(df, outlier_cols)
    
    # 5. Missing Data Handling (short vs long gaps)
    cols_to_interpolate = [
        'rpm', 'load_pct', 'fuel_consumption_lph', 'coolant_temp_c', 
        'oil_pressure_bar', 'exhaust_temp_c', 'exhaust_temp_dev_c', 
        'vibration_mm_s', 'voltage_v', 'current_a', 'frequency_hz'
    ]
    df = handle_missing_data(df, cols_to_interpolate, max_interp_limit=3)
    
    # Forward fill ground truth labels
    df['anomaly_label'] = df['anomaly_label'].ffill()
    df['anomaly_type'] = df['anomaly_type'].ffill()
    
    return df

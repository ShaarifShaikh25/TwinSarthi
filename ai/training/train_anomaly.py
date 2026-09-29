"""
Training script for Station-Wide Anomaly Detector.
"""
import pandas as pd
import json
from ai.models.anomaly_detector import AnomalyDetector

def train_anomaly_detector(df: pd.DataFrame):
    """
    Trains and returns the POLAR-TWIN anomaly detector.
    """
    # Explicit feature list
    features = [
        "temperature_c",
        "wind_speed_mps",
        "humidity_percent",
        "power_consumption_kw",
        "hvac_load_kw",
        "generator_load_percent",
        "fuel_consumption_lph",
        "fuel_level_liters",
        "runtime_hours",
        "generator_load_fraction",
        "hvac_to_power_ratio",
        "temperature_deviation",
        "power_consumption_kw_lag_1",
        "power_consumption_kw_lag_6",
        "generator_load_percent_lag_1",
        "generator_load_percent_lag_6",
        "fuel_consumption_lph_rolling_mean_6",
        "temperature_c_rolling_mean_6"
    ]
    
    # Filter valid columns
    features = [f for f in features if f in df.columns]
    
    # Drop rows with NaN (warm-up rows from lags/rolling)
    df_clean = df.dropna(subset=features).copy()
    
    if len(df_clean) == 0:
        raise ValueError("Insufficient data to train after dropping NaN warm-up rows.")
        
    # Fit detector
    detector = AnomalyDetector(random_state=42, contamination="auto")
    detector.fit(df_clean[features])
    
    return detector

if __name__ == "__main__":
    from simulator.scenarios.normal import generate_normal_scenario
    from ai.preprocessing.feature_engineering import build_ml_features
    
    print("Generating demo data...")
    records = generate_normal_scenario(periods=100, interval_minutes=60, seed=42)
    df = build_ml_features(records)
    
    print("Training anomaly detector...")
    detector = train_anomaly_detector(df)
    
    print("Testing on normal data (first row):")
    sample_normal = df.dropna(subset=detector.features).iloc[[0]]
    normal_result = detector.detect(sample_normal)[0]
    print(json.dumps(normal_result, indent=2))
    
    print("\nTesting on artificial multi-signal anomaly data:")
    # Artificial anomaly: super high load, weird temp
    sample_abnormal = sample_normal.copy()
    sample_abnormal["generator_load_percent"] = 105.0 # Physics anomaly
    sample_abnormal["power_consumption_kw"] = 500.0   # ML anomaly
    sample_abnormal["temperature_c"] = -85.0          # ML anomaly
    
    abnormal_result = detector.detect(sample_abnormal)[0]
    print(json.dumps(abnormal_result, indent=2))
    
    print("\nSignal contribution for artificial anomaly (top 3):")
    contrib = detector.get_signal_contribution(sample_abnormal)[0]
    top_3 = {k: contrib[k] for k in list(contrib.keys())[:3]}
    print(json.dumps(top_3, indent=2))

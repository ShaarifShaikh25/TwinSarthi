"""
SYNTHETIC DATA GENERATION MODULE
Project: POLAR-TWIN
Role: Facility Predictive Maintenance
Asset: Diesel Generator

Generates synthetic telemetry data for normal operation and various anomaly scenarios:
- Combustion Degradation
- Communication Gaps
- Sensor Faults

Note: Numerical operating ranges are engineering assumptions for simulation.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
class GeneratorConfig:
    def __init__(self):
        self.num_samples = 2880 # 2 days at 1 min interval
        self.interval_minutes = 1
        self.start_time = datetime(2026, 1, 1, 0, 0, 0)
        self.seed = 42

def generate_normal_data(config: GeneratorConfig) -> pd.DataFrame:
    np.random.seed(config.seed)
    timestamps = [config.start_time + timedelta(minutes=i * config.interval_minutes) for i in range(config.num_samples)]
    
    steps = np.random.normal(0, 2, config.num_samples)
    load_pct = np.clip(60 + np.cumsum(steps), 30, 90)
    
    rpm = 1500 - (load_pct - 50) * 0.2 + np.random.normal(0, 2, config.num_samples)
    frequency_hz = rpm / 30.0 + np.random.normal(0, 0.05, config.num_samples)
    
    voltage_v = 400 + np.random.normal(0, 1.5, config.num_samples)
    current_a = (load_pct / 100.0) * 800 + np.random.normal(0, 5, config.num_samples)
    
    fuel_consumption_lph = 15 + (load_pct * 0.6) + np.random.normal(0, 1.0, config.num_samples)
    exhaust_temp_c = 300 + (load_pct * 3.5) + np.random.normal(0, 10, config.num_samples)
    exhaust_temp_dev_c = np.random.uniform(5, 12, config.num_samples) + np.random.normal(0, 1, config.num_samples)
    
    coolant_base = 75 + (load_pct * 0.15)
    coolant_temp_c = pd.Series(coolant_base).ewm(span=30).mean().values + np.random.normal(0, 0.5, config.num_samples)
    
    oil_pressure_bar = 5.0 - (coolant_temp_c - 75) * 0.02 + np.random.normal(0, 0.1, config.num_samples)
    vibration_mm_s = 2.0 + (load_pct * 0.01) + np.random.normal(0, 0.2, config.num_samples)
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'rpm': rpm,
        'load_pct': load_pct,
        'fuel_consumption_lph': fuel_consumption_lph,
        'coolant_temp_c': coolant_temp_c,
        'oil_pressure_bar': oil_pressure_bar,
        'exhaust_temp_c': exhaust_temp_c,
        'exhaust_temp_dev_c': exhaust_temp_dev_c,
        'vibration_mm_s': vibration_mm_s,
        'voltage_v': voltage_v,
        'current_a': current_a,
        'frequency_hz': frequency_hz,
        'anomaly_label': 0,
        'anomaly_type': 'NORMAL'
    })
    return df

def inject_combustion_imbalance(df: pd.DataFrame, start_idx: int, degradation_period: int) -> pd.DataFrame:
    df_anomaly = df.copy()
    num_samples = len(df)
    
    for i in range(start_idx, num_samples):
        severity = min((i - start_idx) / degradation_period, 1.0)
        df_anomaly.loc[i, 'exhaust_temp_dev_c'] += severity * 45.0
        df_anomaly.loc[i, 'vibration_mm_s'] += severity * 4.5
        df_anomaly.loc[i, 'fuel_consumption_lph'] *= (1 + (severity * 0.12))
        
        df_anomaly.loc[i, 'anomaly_label'] = 1
        df_anomaly.loc[i, 'anomaly_type'] = 'COMBUSTION_DEGRADATION'
        
    return df_anomaly

def inject_communication_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simulates intermittent Antarctic connectivity by dropping random chunks of rows.
    """
    df_gap = df.copy()
    np.random.seed(42)
    
    # Introduce 5 communication blackouts of random length between 30 mins and 2 hours
    drop_indices = []
    num_gaps = 5
    for _ in range(num_gaps):
        gap_start = np.random.randint(100, len(df) - 150)
        gap_length = np.random.randint(30, 120)
        drop_indices.extend(range(gap_start, gap_start + gap_length))
        
    # We must explicitly drop by index, then sort/reset
    # Drop duplicates in case ranges overlapped
    drop_indices = list(set(drop_indices))
    df_gap = df_gap.drop(index=drop_indices).reset_index(drop=True)
    
    df_gap['anomaly_type'] = 'COMMUNICATION_GAP'
    return df_gap

def inject_sensor_fault(df: pd.DataFrame, start_idx: int) -> pd.DataFrame:
    """
    Simulates a single isolated sensor fault (e.g. coolant temperature sensor wiring issue).
    This helps the model distinguish between a machine fault and a sensor fault.
    """
    df_sensor = df.copy()
    
    # Sensor becomes extremely noisy and drifts unnaturally
    noise = np.random.normal(0, 15, len(df) - start_idx)
    drift = np.linspace(0, 40, len(df) - start_idx)
    
    df_sensor.loc[start_idx:, 'coolant_temp_c'] += (noise + drift)
    
    df_sensor.loc[start_idx:, 'anomaly_label'] = 1
    df_sensor.loc[start_idx:, 'anomaly_type'] = 'SENSOR_FAULT'
    
    return df_sensor

def validate_data(df: pd.DataFrame, name: str):
    print(f"\n--- Validation: {name} ---")
    print(f"Total Rows: {len(df)}")
    
    is_monotonic = True
    if len(df) > 1:
        # Check if timestamps are monotonically increasing (ignoring gaps)
        time_diffs = df['timestamp'].diff().dropna()
        is_monotonic = (time_diffs.dt.total_seconds() > 0).all()
        
    print(f"Timestamp Ordering Valid: {is_monotonic}")
    print(f"Missing Values: {df.isnull().sum().sum()}")
    print(f"Anomaly Types:\n{df['anomaly_type'].value_counts().to_string()}")

def main():
    config = GeneratorConfig()
    output_dir = Path(__file__).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Normal Dataset
    df_normal = generate_normal_data(config)
    df_normal.to_csv(output_dir / 'generator_normal.csv', index=False)
    
    # 2. Combustion Degradation
    start_idx = int(config.num_samples * 0.5)
    df_degradation = inject_combustion_imbalance(df_normal, start_idx, degradation_period=360)
    df_degradation.to_csv(output_dir / 'generator_combustion_degradation.csv', index=False)
    
    # 3. Communication Gap
    df_comm_gap = inject_communication_gap(df_normal)
    df_comm_gap.to_csv(output_dir / 'generator_communication_gap.csv', index=False)
    
    # 4. Sensor Fault (starts at 60% mark)
    df_sensor_fault = inject_sensor_fault(df_normal, int(config.num_samples * 0.6))
    df_sensor_fault.to_csv(output_dir / 'generator_sensor_fault.csv', index=False)
    
    print(f"Successfully generated 4 datasets in {output_dir}")
    
    validate_data(df_normal, "Dataset A: Normal")
    validate_data(df_degradation, "Dataset B: Combustion Degradation")
    validate_data(df_comm_gap, "Dataset C: Communication Gap")
    validate_data(df_sensor_fault, "Dataset D: Sensor Fault")

if __name__ == "__main__":
    main()

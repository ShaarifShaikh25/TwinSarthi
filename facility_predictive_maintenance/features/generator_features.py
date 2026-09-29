import pandas as pd
from pathlib import Path
import sys

# Ensure project root is in path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from preprocessing.generator_preprocessing import preprocess_generator_data

def extract_generator_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts physics-informed, temporal, and cross-sensor features.
    """
    df_feat = df.copy()
    
    # 1. Load-related
    df_feat['load_change_rate'] = df_feat['load_pct'].diff()
    df_feat['rolling_load_mean_30m'] = df_feat['load_pct'].rolling(window=30, min_periods=1).mean()
    df_feat['rolling_load_std_30m'] = df_feat['load_pct'].rolling(window=30, min_periods=1).std().fillna(0)
    
    # 2. Physics-Informed Fuel Features (Load-Adjusted)
    # ENGINEERING ASSUMPTION: Baseline fuel = 15 + load * 0.6
    df_feat['expected_fuel_consumption_lph'] = 15 + (df_feat['load_pct'] * 0.6)
    df_feat['load_adjusted_fuel_deviation'] = df_feat['fuel_consumption_lph'] - df_feat['expected_fuel_consumption_lph']
    df_feat['fuel_efficiency_proxy'] = df_feat['load_pct'] / df_feat['fuel_consumption_lph'].replace(0, pd.NA)
    
    # 3. Thermal Features
    df_feat['exhaust_temp_rolling_mean_15m'] = df_feat['exhaust_temp_c'].rolling(window=15, min_periods=1).mean()
    df_feat['exhaust_temp_rate_c_per_min'] = df_feat['exhaust_temp_c'].diff()
    
    df_feat['coolant_temp_rolling_mean_15m'] = df_feat['coolant_temp_c'].rolling(window=15, min_periods=1).mean()
    df_feat['coolant_temp_rate_c_per_min'] = df_feat['coolant_temp_c'].diff()
    
    # 4. Vibration Features
    df_feat['vibration_rolling_mean_30m'] = df_feat['vibration_mm_s'].rolling(window=30, min_periods=1).mean()
    df_feat['vibration_trend'] = df_feat['vibration_mm_s'].diff(periods=15) # Change over 15 mins
    
    # 5. Oil Pressure Features
    df_feat['oil_pressure_rate_of_change'] = df_feat['oil_pressure_bar'].diff()
    
    # 6. Cross-Sensor & Combustion Degradation Signature
    # ENGINEERING HYPOTHESIS: High exhaust temp dev + positive fuel deviation + rising vibration = combustion stress
    # Normalized roughly to combine signals
    norm_fuel_dev = df_feat['load_adjusted_fuel_deviation'] / 2.0
    norm_exh_dev = df_feat['exhaust_temp_dev_c'] / 10.0 
    df_feat['combustion_signature_proxy'] = norm_fuel_dev + norm_exh_dev + df_feat['vibration_trend'].fillna(0)
    df_feat['combustion_signature_rolling_1h'] = df_feat['combustion_signature_proxy'].rolling(60, min_periods=1).mean()
    
    return df_feat

def main():
    raw_dir = Path("facility_predictive_maintenance/data/synthetic/generator")
    out_dir = Path("facility_predictive_maintenance/data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    datasets = [
        "generator_normal.csv",
        "generator_combustion_degradation.csv",
        "generator_communication_gap.csv",
        "generator_sensor_fault.csv"
    ]
    
    for ds in datasets:
        csv_path = raw_dir / ds
        if not csv_path.exists():
            continue
            
        # Preprocess
        df_clean = preprocess_generator_data(str(csv_path), ds)
        
        # Extract Features
        df_features = extract_generator_features(df_clean)
        
        # Save
        out_path = out_dir / ds.replace('.csv', '_features.csv')
        df_features.to_csv(out_path, index=False)
        
        print(f"-> Saved model-ready dataset to {out_path} with shape {df_features.shape}")
        if ds == "generator_combustion_degradation.csv":
            print("\nSample features (Load-Adjusted Fuel & Combustion Signature):")
            print(df_features[['timestamp', 'load_adjusted_fuel_deviation', 'combustion_signature_rolling_1h']].tail())

if __name__ == "__main__":
    main()

"""
Training script for Energy Forecaster.
"""
import pandas as pd
import json
from ai.models.energy_forecaster import EnergyForecaster

def train_energy_model(df: pd.DataFrame):
    """
    Trains and evaluates the energy forecasting model.
    """
    features = [
        "temperature_c",
        "wind_speed_mps",
        "humidity_percent",
        "hvac_load_kw",
        "generator_load_percent",
        "runtime_hours",
        "fuel_level_liters",
        "temperature_deviation",
        "generator_load_fraction",
        "hvac_to_power_ratio",
        "power_consumption_kw_lag_1",
        "power_consumption_kw_lag_3",
        "power_consumption_kw_lag_6",
        "power_consumption_kw_rolling_mean_6",
        "power_consumption_kw_rolling_std_6",
        "temperature_c_lag_1",
        "temperature_c_lag_6",
        "generator_load_percent_lag_1",
        "generator_load_percent_lag_6"
    ]
    
    # Filter for columns that actually exist in the dataframe
    features = [f for f in features if f in df.columns]
    
    df = df.copy()
    target = "power_consumption_kw_future_1"
    
    # Construct future target strictly per station
    df[target] = df.groupby("station_id")["power_consumption_kw"].shift(-1)
    
    # Remove warm-up rows (NaN in historical lag/rolling) and the final row (NaN in future target)
    df_clean = df.dropna(subset=features + [target])
    
    if len(df_clean) == 0:
        raise ValueError("Insufficient data to train after dropping NaN warm-up rows.")
        
    # Ensure strict chronological order before split
    df_clean = df_clean.sort_values(by="timestamp").reset_index(drop=True)
    
    # Chronological Split (80/20)
    split_idx = int(len(df_clean) * 0.8)
    if split_idx == 0:
        split_idx = 1 # Guarantee at least 1 train row for tiny tests
        
    train_df = df_clean.iloc[:split_idx]
    test_df = df_clean.iloc[split_idx:]
    
    # Train
    model = EnergyForecaster(random_state=42)
    model.fit(train_df[features], train_df[target])
    
    # Evaluate
    # If test_df is empty (e.g. tiny test set), evaluate on train
    eval_df = test_df if len(test_df) > 0 else train_df
    metrics = model.evaluate(eval_df[features], eval_df[target])
    importance = model.get_feature_importance()
    
    return model, metrics, importance

if __name__ == "__main__":
    from simulator.scenarios.normal import generate_normal_scenario
    from ai.preprocessing.feature_engineering import build_ml_features
    
    print("Generating demo data...")
    records = generate_normal_scenario(periods=100, interval_minutes=60, seed=42)
    df = build_ml_features(records)
    
    print("Training energy model...")
    model, metrics, importance = train_energy_model(df)
    
    print("\nEnergy Model Metrics (Performance on synthetic/demo telemetry):")
    print(json.dumps(metrics, indent=2))
    print("\nTop 5 Feature Importances:")
    top_5 = {k: importance[k] for k in list(importance.keys())[:5]}
    print(json.dumps(top_5, indent=2))

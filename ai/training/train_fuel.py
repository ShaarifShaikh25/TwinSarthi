"""
Training script for Fuel Predictor.
"""
import pandas as pd
import json
from ai.models.fuel_predictor import FuelPredictor

def train_fuel_model(df: pd.DataFrame):
    """
    Trains and evaluates the fuel prediction model.
    """
    features = [
        "fuel_level_liters",
        "fuel_consumption_lph",
        "fuel_consumption_lpd",
        "fuel_days_remaining",
        "generator_load_percent",
        "generator_load_fraction",
        "power_consumption_kw",
        "temperature_c",
        "wind_speed_mps",
        "hvac_load_kw",
        "runtime_hours",
        "fuel_level_liters_lag_1",
        "fuel_level_liters_lag_3",
        "fuel_level_liters_lag_6",
        "fuel_consumption_lph_rolling_mean_6",
        "fuel_consumption_lph_rolling_std_6",
        "generator_load_percent_lag_1",
        "generator_load_percent_lag_6"
    ]
    
    # Filter for columns that actually exist in the dataframe
    features = [f for f in features if f in df.columns]
    
    df = df.copy()
    target = "fuel_consumption_lph_future_1"
    
    # Construct future target strictly per station
    df[target] = df.groupby("station_id")["fuel_consumption_lph"].shift(-1)
    
    # Remove warm-up rows and final row
    df_clean = df.dropna(subset=features + [target])
    
    if len(df_clean) == 0:
        raise ValueError("Insufficient data to train after dropping NaN warm-up rows.")
        
    # Chronological Split
    df_clean = df_clean.sort_values(by="timestamp").reset_index(drop=True)
    
    split_idx = int(len(df_clean) * 0.8)
    if split_idx == 0:
        split_idx = 1
        
    train_df = df_clean.iloc[:split_idx]
    test_df = df_clean.iloc[split_idx:]
    
    # Train
    model = FuelPredictor(random_state=42)
    model.fit(train_df[features], train_df[target])
    
    # Evaluate
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
    
    print("Training fuel model...")
    model, metrics, importance = train_fuel_model(df)
    
    print("\nFuel Model Metrics (Performance on synthetic/demo telemetry):")
    print(json.dumps(metrics, indent=2))
    print("\nTop 5 Feature Importances:")
    top_5 = {k: importance[k] for k in list(importance.keys())[:5]}
    print(json.dumps(top_5, indent=2))

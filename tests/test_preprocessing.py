import pytest
import pandas as pd
import numpy as np
from ai.preprocessing.clean_data import flatten_telemetry, handle_missing_values, handle_outliers
from ai.preprocessing.feature_engineering import build_ml_features, create_time_features, create_lag_features, create_rolling_features, create_domain_features
from ai.preprocessing.normalize import fit_scaler, transform_with_scaler, normalize_features
from simulator.scenarios.normal import generate_normal_scenario

@pytest.fixture
def sample_records():
    # Use deterministic seed
    return generate_normal_scenario(periods=10, interval_minutes=60, seed=42)

def test_flattening(sample_records):
    df = flatten_telemetry(sample_records)
    # 1. Nested records flatten
    # 2. Required columns exist
    # 3. Timestamp becomes datetime
    assert isinstance(df, pd.DataFrame)
    assert "temperature_c" in df.columns
    assert "power_consumption_kw" in df.columns
    assert "food_quantity" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    
def test_sorting_and_station_id(sample_records):
    df = flatten_telemetry(sample_records)
    # 4. Records sorted chronologically
    assert df["timestamp"].is_monotonic_increasing
    # 5. Station IDs preserved
    assert all(df["station_id"] == "MAITRI")

def test_missing_values():
    records = [
        {"timestamp": "2026-01-01T00:00:00", "station_id": "MAITRI", "environment": {"temperature_c": -10.0}},
        {"timestamp": "2026-01-01T01:00:00", "station_id": "MAITRI", "environment": {}}, # missing temp
        {"timestamp": "2026-01-01T02:00:00", "station_id": "MAITRI"} # missing cat
    ]
    df = flatten_telemetry(records)
    # Inject an empty categorical for test
    df["weather_condition"] = ["NORMAL", np.nan, np.nan]
    
    df_clean = handle_missing_values(df)
    
    # 6. Missing numeric handled (forward fill)
    assert df_clean.loc[1, "temperature_c"] == -10.0
    # 7. Missing categorical handled
    assert df_clean.loc[1, "weather_condition"] == "NORMAL"
    assert df_clean.loc[2, "weather_condition"] == "NORMAL"

def test_outliers_and_impossible_values():
    records = [{"timestamp": "2026-01-01T00:00:00", "station_id": "MAITRI", 
                "environment": {"temperature_c": -90.0, "humidity_percent": -5.0},
                "fuel": {"level_liters": -100.0}}]
    df = flatten_telemetry(records)
    df_out = handle_outliers(df)
    
    # 8. Impossible values flagged/rejected
    assert df_out.loc[0, "impossible_env_flag"] == True
    assert df_out.loc[0, "impossible_fuel_flag"] == True
    
    # 9. Negative fuel not silently treated as valid
    assert pd.isna(df_out.loc[0, "fuel_level_liters"])

def test_time_features(sample_records):
    df = flatten_telemetry(sample_records)
    df = create_time_features(df)
    # 10. Time features generated
    assert "hour" in df.columns
    assert "day_of_year" in df.columns
    assert "hour_sin" in df.columns

def test_lag_features():
    df = pd.DataFrame({
        "station_id": ["MAITRI"] * 5,
        "power_consumption_kw": [10, 20, 30, 40, 50]
    })
    df_lag = create_lag_features(df)
    # 11. Lag features don't use future data
    assert pd.isna(df_lag.loc[0, "power_consumption_kw_lag_1"])
    assert df_lag.loc[1, "power_consumption_kw_lag_1"] == 10
    assert df_lag.loc[4, "power_consumption_kw_lag_3"] == 20

def test_rolling_features():
    df = pd.DataFrame({
        "station_id": ["MAITRI"] * 10,
        "power_consumption_kw": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    })
    df_roll = create_rolling_features(df)
    # 12. Rolling features (Uses shift(1) so current value isn't included)
    assert pd.isna(df_roll.loc[0, "power_consumption_kw_rolling_mean_6"])
    assert df_roll.loc[1, "power_consumption_kw_rolling_mean_6"] == 10.0
    assert df_roll.loc[2, "power_consumption_kw_rolling_mean_6"] == 15.0 # (10+20)/2

def test_domain_features():
    df = pd.DataFrame({
        "generator_load_percent": [50.0],
        "hvac_load_kw": [20.0],
        "power_consumption_kw": [0.0], # Test div by zero
        "temperature_c": [-20.0]
    })
    df_dom = create_domain_features(df)
    # 13. Div by zero handled
    assert df_dom.loc[0, "hvac_to_power_ratio"] == 0.0
    # 14. Domain features generated
    assert df_dom.loc[0, "generator_load_fraction"] == 0.5
    assert df_dom.loc[0, "temperature_deviation"] == -5.0

def test_build_ml_features(sample_records):
    # 15. build_ml_features returns DataFrame
    df = build_ml_features(sample_records)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "power_consumption_kw_lag_1" in df.columns
    assert "power_consumption_kw_rolling_mean_6" in df.columns
    # Check that lag columns have some NaNs for warm-up rows
    assert df["power_consumption_kw_lag_1"].isna().sum() > 0

def test_normalization():
    df_train = pd.DataFrame({"feat1": [1, 2, 3], "feat2": [4, 5, 6]})
    df_test = pd.DataFrame({"feat1": [4], "feat2": [7]})
    
    scaled_train, scaled_test, scaler = normalize_features(df_train, df_test, ["feat1", "feat2"])
    
    # 16. Normalization works
    assert np.isclose(scaled_train["feat1"].mean(), 0.0)
    
    # 17. Scaler transforms unseen data without refitting
    # The mean of train feat1 is 2, std is ~0.816. Test feat1 is 4, so it should be > 0
    assert scaled_test["feat1"].iloc[0] > 1.0

if __name__ == '__main__':
    pytest.main(["-v", __file__])

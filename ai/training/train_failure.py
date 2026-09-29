"""
Training / Calibration script for Equipment Failure Predictors.
Sets baseline rules and statistics for the health index logic.
"""
import pandas as pd
import json
from ai.models.equipment_failure import EquipmentFailurePredictor

def calibrate_failure_predictors(df: pd.DataFrame):
    """
    Calibrates baseline prototype statistics for GENERATOR and HVAC predictors.
    """
    # Instantiate
    gen_predictor = EquipmentFailurePredictor(equipment_type="GENERATOR")
    hvac_predictor = EquipmentFailurePredictor(equipment_type="HVAC")
    
    # Fit/Calibrate
    gen_predictor.fit(df)
    hvac_predictor.fit(df)
    
    return gen_predictor, hvac_predictor

if __name__ == "__main__":
    from simulator.scenarios.normal import generate_normal_scenario
    from ai.preprocessing.feature_engineering import build_ml_features
    from ai.training.train_anomaly import train_anomaly_detector
    
    print("Generating demo data...")
    records = generate_normal_scenario(periods=100, interval_minutes=60, seed=42)
    df = build_ml_features(records)
    
    # Optionally get step 5 anomaly info
    detector = train_anomaly_detector(df)
    anom_scores = detector.score(df)
    df["anomaly_score"] = anom_scores
    
    print("Calibrating Equipment Health logic...")
    gen_pred, hvac_pred = calibrate_failure_predictors(df)
    
    print("\nTesting Normal Generator row:")
    sample = df.iloc[[90]]
    res_gen = gen_pred.predict(sample)[0]
    print(json.dumps(res_gen, indent=2))
    
    print("\nTesting Artificial Degraded Generator row:")
    degraded = sample.copy()
    degraded["generator_load_percent"] = 92.0 # High load
    degraded["generator_load_percent_rolling_mean_6"] = 70.0 # Huge jump -> DEGRADING
    degraded["anomaly_score"] = 0.85 # Flagged by Step 5
    degraded["runtime_hours"] = 4800.0 # Approaching 5000 max
    
    res_deg = gen_pred.predict(degraded)[0]
    print(json.dumps(res_deg, indent=2))
    
    print("\nTesting Normal HVAC row (Cold weather -> High Load):")
    hvac_normal = sample.copy()
    hvac_normal["temperature_c"] = -40.0
    hvac_normal["hvac_load_kw"] = 120.0
    res_hvac1 = hvac_pred.predict(hvac_normal)[0]
    print(json.dumps(res_hvac1, indent=2))
    
    print("\nTesting Abnormal HVAC row (Warm weather -> High Load):")
    hvac_abnormal = sample.copy()
    hvac_abnormal["temperature_c"] = -5.0
    hvac_abnormal["hvac_load_kw"] = 120.0
    res_hvac2 = hvac_pred.predict(hvac_abnormal)[0]
    print(json.dumps(res_hvac2, indent=2))

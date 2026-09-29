import pytest
import pandas as pd
from ai.models.equipment_failure import EquipmentFailurePredictor
from ai.training.train_failure import calibrate_failure_predictors
from simulator.scenarios.normal import generate_normal_scenario
from ai.preprocessing.feature_engineering import build_ml_features

@pytest.fixture(scope="module")
def ml_ready_data():
    records = generate_normal_scenario(periods=20, interval_minutes=60, seed=42)
    df = build_ml_features(records)
    df["anomaly_score"] = 0.0 # Mock step 5
    return df

@pytest.fixture(scope="module")
def predictors(ml_ready_data):
    return calibrate_failure_predictors(ml_ready_data)

def test_initialization(predictors):
    gen_pred, hvac_pred = predictors
    # 1. Generator predictor initializes
    assert gen_pred.equipment_type == "GENERATOR"
    # 2. HVAC predictor initializes
    assert hvac_pred.equipment_type == "HVAC"
    
def test_score_ranges(predictors, ml_ready_data):
    gen_pred, _ = predictors
    sample = ml_ready_data.iloc[[0]]
    res = gen_pred.predict(sample)[0]
    
    # 3. Health score is 0-100
    assert 0.0 <= res["health_score"] <= 100.0
    # 4. Failure-risk score is 0-1
    assert 0.0 <= res["failure_risk_score"] <= 1.0

def test_normal_generator(predictors, ml_ready_data):
    gen_pred, _ = predictors
    sample = ml_ready_data.iloc[[0]].copy()
    sample["generator_load_percent"] = 50.0
    sample["generator_load_percent_rolling_mean_6"] = 50.0
    
    res = gen_pred.predict(sample)[0]
    # 5. Normal generator -> healthy/monitor
    assert res["status"] in ["HEALTHY", "MONITOR"]
    assert res["maintenance_priority"] == "LOW"

def test_degrading_generator(predictors, ml_ready_data):
    gen_pred, _ = predictors
    
    sample_norm = ml_ready_data.iloc[[0]].copy()
    sample_norm["generator_load_percent"] = 50.0
    sample_norm["generator_load_percent_rolling_mean_6"] = 50.0
    res_norm = gen_pred.predict(sample_norm)[0]
    
    sample_deg = ml_ready_data.iloc[[0]].copy()
    sample_deg["generator_load_percent"] = 90.0
    sample_deg["generator_load_percent_rolling_mean_6"] = 70.0 # 90 > 70*1.05
    sample_deg["runtime_hours"] = 4900.0
    sample_deg["anomaly_score"] = 0.9 # Repeated anomaly evidence
    
    res_deg = gen_pred.predict(sample_deg)[0]
    
    # 6. Degrading generator -> higher risk
    assert res_deg["failure_risk_score"] > res_norm["failure_risk_score"]
    # 7. Degradation trend works
    assert res_deg["degradation_trend"] == "DEGRADING"
    # 8. Increasing load detected
    assert any("load trend is increasing/degrading" in f for f in res_deg["risk_factors"])
    # 12. Maintenance priority generated
    assert res_deg["maintenance_priority"] in ["MEDIUM", "HIGH", "CRITICAL"]
    # 14. Repeated anomaly evidence can increase risk
    assert any("Repeated abnormal" in f for f in res_deg["risk_factors"])

def test_hvac_logic(predictors, ml_ready_data):
    _, hvac_pred = predictors
    
    # 10. HVAC high load under cold weather is NOT automatically classified as failure
    cold_normal = ml_ready_data.iloc[[0]].copy()
    cold_normal["temperature_c"] = -50.0
    cold_normal["hvac_load_kw"] = 100.0 # High absolute, but temp is freezing
    cold_normal["power_consumption_kw_rolling_mean_6"] = 250.0 # Normal trend
    
    res_cold = hvac_pred.predict(cold_normal)[0]
    
    # 11. Abnormally high HVAC demand under warm weather increases risk
    warm_abnormal = ml_ready_data.iloc[[0]].copy()
    warm_abnormal["temperature_c"] = -2.0
    warm_abnormal["hvac_load_kw"] = 100.0 # Same high load, but warm weather!
    warm_abnormal["power_consumption_kw_rolling_mean_6"] = 250.0
    
    res_warm = hvac_pred.predict(warm_abnormal)[0]
    
    assert res_warm["failure_risk_score"] > res_cold["failure_risk_score"]
    # 13. Risk factors explainable
    assert any("unusually high relative to environmental temperature" in f for f in res_warm["risk_factors"])

if __name__ == '__main__':
    pytest.main(["-v", __file__])

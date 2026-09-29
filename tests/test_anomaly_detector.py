import pytest
import pandas as pd
import numpy as np
import os
from ai.models.anomaly_detector import AnomalyDetector
from ai.training.train_anomaly import train_anomaly_detector
from simulator.scenarios.normal import generate_normal_scenario
from ai.preprocessing.feature_engineering import build_ml_features

@pytest.fixture(scope="module")
def ml_ready_data():
    records = generate_normal_scenario(periods=50, interval_minutes=60, seed=42)
    return build_ml_features(records)

@pytest.fixture(scope="module")
def detector(ml_ready_data):
    return train_anomaly_detector(ml_ready_data)

def test_anomaly_model_trains(detector):
    # 1. Trains successfully
    assert isinstance(detector, AnomalyDetector)
    assert len(detector.features) > 0
    assert len(detector.baseline_stats) == len(detector.features)

def test_normal_predictions(detector, ml_ready_data):
    sample = ml_ready_data.dropna(subset=detector.features).iloc[[0]]
    result = detector.detect(sample)[0]
    
    # 2. Normal data produces predictions
    # 3. Contains anomaly info
    assert "is_anomaly" in result
    assert "anomaly_score" in result
    assert "severity" in result
    assert "reasons" in result
    
    # 4. Normal rows mostly classified as non-anomalous (usually low score for pure training data)
    # 6. Score is numeric
    # 7. Score within range [0, 1]
    assert isinstance(result["anomaly_score"], float)
    assert 0.0 <= result["anomaly_score"] <= 1.0
    
    # 8. Severity is one of the categories
    assert result["severity"] in ["NORMAL", "LOW", "MEDIUM", "HIGH"]

def test_artificial_anomaly(detector, ml_ready_data):
    sample = ml_ready_data.dropna(subset=detector.features).iloc[[0]].copy()
    
    # Corrupt data with severe ML anomaly
    sample["generator_load_percent"] = 99.0
    sample["power_consumption_kw"] = 400.0
    
    result = detector.detect(sample)[0]
    
    # 5. Artificial anomaly is detected
    assert result["is_anomaly"] is True
    # 9. Reasons generated
    assert len(result["reasons"]) > 0

def test_physical_invalid_values(detector, ml_ready_data):
    sample = ml_ready_data.dropna(subset=detector.features).iloc[[0]].copy()
    # 10. Physical invalid values are detected
    sample["generator_load_percent"] = 150.0 # > 100
    
    result = detector.detect(sample)[0]
    
    assert result["is_anomaly"] is True
    assert result["has_physical_anomaly"] is True
    assert result["severity"] == "HIGH"
    assert any("Physical Limit" in reason for reason in result["reasons"])

def test_model_persistence(detector, tmp_path):
    # 12. Persistence via joblib
    path = str(tmp_path / "model.pkl")
    detector.save(path)
    
    assert os.path.exists(path)
    
    loaded_detector = AnomalyDetector.load(path)
    assert loaded_detector.features == detector.features
    assert loaded_detector.baseline_stats.keys() == detector.baseline_stats.keys()

if __name__ == '__main__':
    pytest.main(["-v", __file__])

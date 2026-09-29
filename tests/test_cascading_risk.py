import pytest
from backend.app.risk_engine.causal_graph import build_default_causal_graph
from backend.app.risk_engine.risk_score import calculate_risk_score
from backend.app.risk_engine.cascading_risk import CascadingRiskEngine

@pytest.fixture
def normal_state():
    return {
        "station_id": "MAITRI",
        "environment": {"temperature_c": -5, "wind_speed_mps": 10},
        "energy": {"generator_load_percent": 45},
        "fuel": {"days_remaining": 20},
        "equipment": {
            "generator": {"failure_risk_score": 0.2, "health_score": 90, "degradation_trend": "STABLE"}
        },
        "anomaly": {"is_anomaly": False, "anomaly_score": 0.1}
    }

@pytest.fixture
def severe_state():
    return {
        "station_id": "BHARATI",
        "environment": {"temperature_c": -20, "wind_speed_mps": 25},
        "energy": {"generator_load_percent": 85},
        "fuel": {"days_remaining": 4},
        "equipment": {
            "generator": {"failure_risk_score": 0.8, "health_score": 30, "degradation_trend": "DEGRADING"}
        },
        "anomaly": {"is_anomaly": True, "anomaly_score": 0.75}
    }

def test_risk_score_range(severe_state):
    # 1. test_risk_score_range
    # 13. test_risk_never_exceeds_100
    # 14. test_risk_never_below_0
    score_info = calculate_risk_score(severe_state)
    assert 0.0 <= score_info["risk_score"] <= 100.0

def test_normal_station_low_risk(normal_state):
    # 2. test_normal_station_low_risk
    engine = CascadingRiskEngine()
    result = engine.evaluate(normal_state)
    assert result["risk_level"] in ["NORMAL", "LOW"]
    assert result["overall_risk_score"] < 30.0

def test_severe_station_high_risk(severe_state, normal_state):
    engine = CascadingRiskEngine()
    norm_res = engine.evaluate(normal_state)
    sev_res = engine.evaluate(severe_state)
    assert sev_res["overall_risk_score"] > norm_res["overall_risk_score"]
    assert sev_res["risk_level"] in ["MEDIUM", "CRITICAL"]

def test_low_temperature_increases_risk(normal_state):
    # 3. test_low_temperature_increases_risk
    engine = CascadingRiskEngine()
    base_res = engine.evaluate(normal_state)
    
    cold_state = normal_state.copy()
    cold_state["environment"] = {"temperature_c": -30}
    cold_res = engine.evaluate(cold_state)
    
    assert cold_res["overall_risk_score"] > base_res["overall_risk_score"]

def test_high_generator_load_increases_risk(normal_state):
    # 4. test_high_generator_load_increases_risk
    engine = CascadingRiskEngine()
    base_res = engine.evaluate(normal_state)
    
    load_state = normal_state.copy()
    load_state["energy"] = {"generator_load_percent": 95}
    load_res = engine.evaluate(load_state)
    
    assert load_res["overall_risk_score"] > base_res["overall_risk_score"]

def test_low_fuel_increases_logistics_risk(normal_state):
    # 5. test_low_fuel_increases_logistics_risk
    engine = CascadingRiskEngine()
    base_res = engine.evaluate(normal_state)
    
    fuel_state = normal_state.copy()
    fuel_state["fuel"] = {"days_remaining": 2}
    fuel_res = engine.evaluate(fuel_state)
    
    assert fuel_res["overall_risk_score"] > base_res["overall_risk_score"]

def test_generator_degradation_increases_risk(normal_state):
    # 6. test_generator_degradation_increases_risk
    engine = CascadingRiskEngine()
    base_res = engine.evaluate(normal_state)
    
    deg_state = normal_state.copy()
    deg_state["equipment"]["generator"]["failure_risk_score"] = 0.95
    deg_res = engine.evaluate(deg_state)
    
    assert deg_res["overall_risk_score"] > base_res["overall_risk_score"]

def test_anomaly_contributes_to_risk(normal_state):
    # 7. test_anomaly_contributes_to_risk
    engine = CascadingRiskEngine()
    base_res = engine.evaluate(normal_state)
    
    anom_state = normal_state.copy()
    anom_state["anomaly"] = {"is_anomaly": True, "anomaly_score": 0.9}
    anom_res = engine.evaluate(anom_state)
    
    assert anom_res["overall_risk_score"] > base_res["overall_risk_score"]

def test_causal_graph_dependencies():
    # 8. test_causal_graph_dependencies
    graph = build_default_causal_graph()
    deps = graph.get_dependencies("energy.hvac")
    assert "environment.temperature" in deps
    
    succ = graph.get_dependents("infrastructure.generator")
    assert "fuel.reserve" in succ

def test_cascade_contains_multiple_steps(severe_state):
    # 9. test_cascade_contains_multiple_steps
    engine = CascadingRiskEngine()
    result = engine.evaluate(severe_state)
    cascade = result["cascade"]
    assert len(cascade) > 2
    
    nodes = [step["node"] for step in cascade]
    # Verify the chain is present
    assert "environment.temperature" in nodes
    assert "energy.hvac" in nodes
    assert "infrastructure.generator" in nodes
    assert "fuel.reserve" in nodes

def test_cascade_explanations_exist(severe_state):
    # 10. test_cascade_explanations_exist
    engine = CascadingRiskEngine()
    result = engine.evaluate(severe_state)
    cascade = result["cascade"]
    for step in cascade:
        assert "impact" in step
        assert len(step["impact"]) > 0

def test_missing_optional_fields():
    # 11. test_missing_optional_fields
    engine = CascadingRiskEngine()
    # Empty state should be handled gracefully
    result = engine.evaluate({})
    assert result["overall_risk_score"] == 0.0
    assert result["risk_level"] == "NORMAL"

def test_deterministic_output(severe_state):
    # 12. test_deterministic_output
    engine = CascadingRiskEngine()
    res1 = engine.evaluate(severe_state)
    res2 = engine.evaluate(severe_state)
    assert res1 == res2

if __name__ == '__main__':
    pytest.main(["-v", __file__])

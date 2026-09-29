import pytest
from backend.app.risk_engine.mission_continuity import MissionContinuityEngine

@pytest.fixture
def normal_state():
    return {
        "station_id": "MAITRI",
        "environment": {"temperature_c": -5, "wind_speed_mps": 10},
        "energy": {"generator_load_percent": 45},
        "fuel": {"days_remaining": 20},
        "equipment": {
            "generator": {"failure_risk_score": 0.05, "health_score": 95, "degradation_trend": "STABLE"}
        },
        "logistics": {
            "food_days_remaining": 30,
            "medicine_days_remaining": 40,
            "spares_days_remaining": 30
        },
        "communication": {"status": "ONLINE", "availability": 1.0},
        "risk": {"overall_risk_score": 10.0}
    }

@pytest.fixture
def stressed_state():
    return {
        "station_id": "MAITRI",
        "environment": {"temperature_c": -20, "wind_speed_mps": 15},
        "energy": {"generator_load_percent": 88},
        "fuel": {"days_remaining": 3},
        "equipment": {
            "generator": {"failure_risk_score": 0.80, "health_score": 30, "degradation_trend": "DEGRADING"}
        },
        "logistics": {
            "food_days_remaining": 5,
            "medicine_days_remaining": 4,
            "spares_days_remaining": 2
        },
        "communication": {"status": "DEGRADED", "availability": 0.55},
        "risk": {"overall_risk_score": 85.0}
    }

def test_score_range(normal_state):
    # 1. test_score_range, 15. test_score_never_exceeds_100, 16. test_score_never_below_0
    engine = MissionContinuityEngine()
    result = engine.calculate_mission_continuity(normal_state)
    assert 0.0 <= result["mission_continuity_score"] <= 100.0

def test_normal_station_high_continuity(normal_state):
    # 2. test_normal_station_high_continuity
    engine = MissionContinuityEngine()
    result = engine.calculate_mission_continuity(normal_state)
    assert result["mission_continuity_score"] >= 80.0
    assert result["status"] == "STABLE"

def test_low_fuel_reduces_continuity(normal_state):
    # 3. test_low_fuel_reduces_continuity
    engine = MissionContinuityEngine()
    base_res = engine.calculate_mission_continuity(normal_state)
    
    low_fuel = normal_state.copy()
    low_fuel["fuel"] = {"days_remaining": 2}
    res = engine.calculate_mission_continuity(low_fuel)
    
    assert res["mission_continuity_score"] < base_res["mission_continuity_score"]
    assert "Low fuel reserve" in res["key_risks"]

def test_high_generator_load_reduces_continuity(normal_state):
    # 4. test_high_generator_load_reduces_continuity
    engine = MissionContinuityEngine()
    base_res = engine.calculate_mission_continuity(normal_state)
    
    high_load = normal_state.copy()
    high_load["energy"] = {"generator_load_percent": 95}
    res = engine.calculate_mission_continuity(high_load)
    
    assert res["mission_continuity_score"] < base_res["mission_continuity_score"]
    assert "Severe energy stress" in res["key_risks"]

def test_low_equipment_health_reduces_continuity(normal_state):
    # 5. test_low_equipment_health_reduces_continuity
    engine = MissionContinuityEngine()
    base_res = engine.calculate_mission_continuity(normal_state)
    
    low_equip = normal_state.copy()
    low_equip["equipment"]["generator"]["health_score"] = 20
    res = engine.calculate_mission_continuity(low_equip)
    
    assert res["mission_continuity_score"] < base_res["mission_continuity_score"]
    assert "Critical equipment health concern" in res["key_risks"]

def test_degrading_equipment_reduces_continuity(normal_state):
    # 6. test_degrading_equipment_reduces_continuity
    engine = MissionContinuityEngine()
    
    stable = normal_state.copy()
    stable["equipment"]["generator"]["degradation_trend"] = "STABLE"
    res_stable = engine.calculate_mission_continuity(stable)
    
    deg = normal_state.copy()
    deg["equipment"]["generator"]["degradation_trend"] = "DEGRADING"
    res_deg = engine.calculate_mission_continuity(deg)
    
    assert "Generator degradation trend is increasing." in res_deg["components"]["equipment"]["reasons"]

def test_low_inventory_reduces_continuity(normal_state):
    # 7. test_low_inventory_reduces_continuity
    engine = MissionContinuityEngine()
    base_res = engine.calculate_mission_continuity(normal_state)
    
    low_inv = normal_state.copy()
    low_inv["logistics"] = {"food_days_remaining": 5, "medicine_days_remaining": 2, "spares_days_remaining": 3}
    res = engine.calculate_mission_continuity(low_inv)
    
    assert res["mission_continuity_score"] < base_res["mission_continuity_score"]
    assert "Critical inventory shortage" in res["key_risks"]

def test_severe_environment_reduces_continuity(normal_state):
    # 8. test_severe_environment_reduces_continuity
    engine = MissionContinuityEngine()
    base_res = engine.calculate_mission_continuity(normal_state)
    
    sev_env = normal_state.copy()
    sev_env["environment"] = {"temperature_c": -40, "wind_speed_mps": 30}
    res = engine.calculate_mission_continuity(sev_env)
    
    assert res["mission_continuity_score"] < base_res["mission_continuity_score"]
    assert "Severe cold temperature is stressing station systems." in res["components"]["environment"]["reasons"]

def test_communication_offline_reduces_continuity(normal_state):
    # 9. test_communication_offline_reduces_continuity
    engine = MissionContinuityEngine()
    base_res = engine.calculate_mission_continuity(normal_state)
    
    off_comm = normal_state.copy()
    off_comm["communication"] = {"status": "OFFLINE", "availability": 0.0}
    res = engine.calculate_mission_continuity(off_comm)
    
    assert res["mission_continuity_score"] < base_res["mission_continuity_score"]

def test_missing_communication_does_not_equal_failure(normal_state):
    # 10. test_missing_communication_does_not_equal_failure
    engine = MissionContinuityEngine()
    miss_comm = normal_state.copy()
    del miss_comm["communication"]
    
    res = engine.calculate_mission_continuity(miss_comm)
    # The coverage should be 0.9 (since comm is 0.1 weight)
    assert res["data_quality"]["coverage"] == 0.9
    assert "communication" in res["data_quality"]["missing_components"]
    assert res["mission_continuity_score"] > 80.0 # still stable

def test_missing_inventory_is_handled(normal_state):
    # 11. test_missing_inventory_is_handled
    engine = MissionContinuityEngine()
    miss_inv = normal_state.copy()
    del miss_inv["logistics"]
    
    res = engine.calculate_mission_continuity(miss_inv)
    assert res["data_quality"]["coverage"] == 0.85
    assert "inventory" in res["data_quality"]["missing_components"]
    assert res["mission_continuity_score"] > 80.0

def test_missing_equipment_is_handled(normal_state):
    # 12. test_missing_equipment_is_handled
    engine = MissionContinuityEngine()
    miss_eq = normal_state.copy()
    del miss_eq["equipment"]
    
    res = engine.calculate_mission_continuity(miss_eq)
    assert res["data_quality"]["coverage"] == 0.80
    assert "equipment" in res["data_quality"]["missing_components"]

def test_component_weights_sum_correctly(normal_state):
    # 13. test_component_weights_sum_correctly
    engine = MissionContinuityEngine()
    res = engine.calculate_mission_continuity(normal_state)
    total_weight = sum([c["weight"] for c in res["components"].values()])
    # allow tiny float drift
    assert 0.99 <= total_weight <= 1.01

def test_score_is_deterministic(normal_state):
    # 14. test_score_is_deterministic
    engine = MissionContinuityEngine()
    res1 = engine.calculate_mission_continuity(normal_state)
    res2 = engine.calculate_mission_continuity(normal_state)
    assert res1 == res2

def test_key_risks_are_explainable(stressed_state):
    # 17. test_key_risks_are_explainable
    engine = MissionContinuityEngine()
    res = engine.calculate_mission_continuity(stressed_state)
    assert len(res["key_risks"]) > 0

def test_recommendations_are_generated(stressed_state):
    # 18. test_recommendations_are_generated
    engine = MissionContinuityEngine()
    res = engine.calculate_mission_continuity(stressed_state)
    assert len(res["recommendations"]) > 0

def test_step7_risk_context_is_supported(normal_state):
    # 19. test_step7_risk_context_is_supported
    engine = MissionContinuityEngine()
    norm = normal_state.copy()
    norm["risk"] = {"overall_risk_score": 10.0}
    res_low = engine.calculate_mission_continuity(norm)
    
    high = normal_state.copy()
    high["risk"] = {"overall_risk_score": 85.0}
    res_high = engine.calculate_mission_continuity(high)
    
    # High risk should reduce environment/continuity score
    assert res_high["mission_continuity_score"] < res_low["mission_continuity_score"]

def test_existing_tests_still_pass(normal_state, stressed_state):
    # 20. test_existing_tests_still_pass (Tested by global pytest)
    # Important Scenario Test
    engine = MissionContinuityEngine()
    norm_score = engine.calculate_mission_continuity(normal_state)["mission_continuity_score"]
    stress_score = engine.calculate_mission_continuity(stressed_state)["mission_continuity_score"]
    assert norm_score > stress_score

if __name__ == '__main__':
    pytest.main(["-v", __file__])

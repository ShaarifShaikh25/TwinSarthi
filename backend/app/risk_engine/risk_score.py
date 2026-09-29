"""
Risk Scoring Logic for POLAR-TWIN.
Transparent, deterministic, bounded scoring without double-counting.
Thresholds are PROTOTYPE assumptions for demonstration.
"""
from typing import Dict, Any, List, Tuple

# PROTOTYPE THRESHOLDS
CONFIG = {
    "TEMP_COLD_THRESHOLD": -15.0,
    "WIND_HIGH_THRESHOLD": 20.0,
    "GENERATOR_HIGH_LOAD": 80.0,
    "FUEL_DAYS_LOW": 7.0,
    "FUEL_DAYS_CRITICAL": 3.0,
    "EQUIP_HEALTH_CONCERN": 40.0,
    "ANOMALY_EVIDENCE_THRESHOLD": 0.5,
    "MAX_CONTRIBUTIONS": {
        "environment": 10.0,
        "energy_load": 20.0,
        "equipment_health": 30.0,
        "fuel_logistics": 25.0,
        "anomaly_evidence": 15.0
    }
}

def _get_env_contribution(state: Dict[str, Any]) -> float:
    env = state.get("environment", {})
    contrib = 0.0
    if env.get("temperature_c", 0) < CONFIG["TEMP_COLD_THRESHOLD"]:
        contrib += 5.0
    if env.get("wind_speed_mps", 0) > CONFIG["WIND_HIGH_THRESHOLD"]:
        contrib += 5.0
    return min(contrib, CONFIG["MAX_CONTRIBUTIONS"]["environment"])

def _get_energy_contribution(state: Dict[str, Any]) -> float:
    energy = state.get("energy", {})
    load = energy.get("generator_load_percent", 0)
    
    if load > CONFIG["GENERATOR_HIGH_LOAD"]:
        # Linearly scale from 80% to 100% up to the max contribution
        excess = min(load - CONFIG["GENERATOR_HIGH_LOAD"], 20.0)
        score = (excess / 20.0) * CONFIG["MAX_CONTRIBUTIONS"]["energy_load"]
        return min(score, CONFIG["MAX_CONTRIBUTIONS"]["energy_load"])
    return 0.0

def _get_equipment_contribution(state: Dict[str, Any]) -> float:
    equip = state.get("equipment", {})
    max_contrib = CONFIG["MAX_CONTRIBUTIONS"]["equipment_health"]
    
    # We take the worst failure risk score across available equipment
    highest_risk = 0.0
    for eq_type, metrics in equip.items():
        if isinstance(metrics, dict):
            risk = metrics.get("failure_risk_score", 0.0)
            if risk > highest_risk:
                highest_risk = risk
                
    return min(highest_risk * max_contrib, max_contrib)

def _get_fuel_contribution(state: Dict[str, Any]) -> float:
    fuel = state.get("fuel", {})
    days = fuel.get("days_remaining", 999.0)
    max_contrib = CONFIG["MAX_CONTRIBUTIONS"]["fuel_logistics"]
    
    if days <= CONFIG["FUEL_DAYS_CRITICAL"]:
        return max_contrib
    elif days <= CONFIG["FUEL_DAYS_LOW"]:
        return max_contrib * 0.6
    return 0.0

def _get_anomaly_contribution(state: Dict[str, Any]) -> float:
    anom = state.get("anomaly", {})
    score = anom.get("anomaly_score", 0.0)
    max_contrib = CONFIG["MAX_CONTRIBUTIONS"]["anomaly_evidence"]
    
    if anom.get("is_anomaly", False) and score > CONFIG["ANOMALY_EVIDENCE_THRESHOLD"]:
        return min(score * max_contrib, max_contrib)
    return 0.0

def _get_risk_level(score: float) -> str:
    if score <= 25.0: return "NORMAL"
    if score <= 50.0: return "LOW"
    if score <= 75.0: return "MEDIUM"
    return "CRITICAL"

def calculate_risk_score(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates overall station risk securely and deterministically.
    Avoids double counting by bounding distinct factor contributions.
    """
    contributors = []
    
    env_c = _get_env_contribution(state)
    if env_c > 0: contributors.append({"factor": "environment", "contribution": round(env_c, 2)})
        
    en_c = _get_energy_contribution(state)
    if en_c > 0: contributors.append({"factor": "generator_load", "contribution": round(en_c, 2)})
        
    eq_c = _get_equipment_contribution(state)
    if eq_c > 0: contributors.append({"factor": "equipment_health", "contribution": round(eq_c, 2)})
        
    fu_c = _get_fuel_contribution(state)
    if fu_c > 0: contributors.append({"factor": "fuel_reserve", "contribution": round(fu_c, 2)})
        
    an_c = _get_anomaly_contribution(state)
    if an_c > 0: contributors.append({"factor": "anomaly_evidence", "contribution": round(an_c, 2)})
        
    total_score = sum([c["contribution"] for c in contributors])
    total_score = min(max(total_score, 0.0), 100.0) # Strictly bounded 0-100
    
    return {
        "risk_score": round(total_score, 2),
        "risk_level": _get_risk_level(total_score),
        "contributors": contributors
    }

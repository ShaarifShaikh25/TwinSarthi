"""
Cascading Risk Engine for POLAR-TWIN.
Transforms state dict into an explainable causal cascade of operational consequences.
"""
from typing import Dict, Any, List
from .causal_graph import build_default_causal_graph
from .risk_score import calculate_risk_score, CONFIG

class CascadingRiskEngine:
    def __init__(self):
        self.graph = build_default_causal_graph()
        
    def _identify_triggers(self, state: Dict[str, Any]) -> List[str]:
        """Identifies root cause triggers that begin the cascade."""
        triggers = []
        env = state.get("environment", {})
        if env.get("temperature_c", 0) < CONFIG["TEMP_COLD_THRESHOLD"]:
            triggers.append("Low temperature")
        if env.get("wind_speed_mps", 0) > CONFIG["WIND_HIGH_THRESHOLD"]:
            triggers.append("High wind speed")
            
        energy = state.get("energy", {})
        if energy.get("generator_load_percent", 0) > CONFIG["GENERATOR_HIGH_LOAD"]:
            triggers.append("High generator load")
            
        equip = state.get("equipment", {})
        for eq, metrics in equip.items():
            if isinstance(metrics, dict) and metrics.get("degradation_trend") == "DEGRADING":
                triggers.append(f"{str(eq).capitalize()} degradation")
                
        anom = state.get("anomaly", {})
        if anom.get("is_anomaly", False):
            triggers.append("Anomalous operational behavior")
            
        return triggers

    def _evaluate_node(self, node: str, state: Dict[str, Any], active_stress: bool) -> Dict[str, Any]:
        """Evaluates a single node's status and impact statement."""
        res = {"node": node, "status": "NORMAL", "impact": "Operating normally"}
        
        if node == "environment.temperature":
            temp = state.get("environment", {}).get("temperature_c", 0)
            if temp < CONFIG["TEMP_COLD_THRESHOLD"]:
                res.update({"status": "HIGH_STRESS", "impact": "Increased heating demand"})
                active_stress = True
                
        elif node == "environment.wind":
            wind = state.get("environment", {}).get("wind_speed_mps", 0)
            if wind > CONFIG["WIND_HIGH_THRESHOLD"]:
                res.update({"status": "HIGH_STRESS", "impact": "Increased structural/heating stress"})
                active_stress = True
                
        elif node == "energy.hvac":
            if active_stress:
                res.update({"status": "HIGH_STRESS", "impact": "HVAC demand increases"})
                
        elif node == "energy.power":
            if active_stress:
                res.update({"status": "ELEVATED", "impact": "Total power consumption increases"})
                
        elif node == "infrastructure.generator":
            load = state.get("energy", {}).get("generator_load_percent", 0)
            equip_health = state.get("equipment", {}).get("generator", {}).get("health_score", 100)
            if active_stress or load > CONFIG["GENERATOR_HIGH_LOAD"] or equip_health < CONFIG["EQUIP_HEALTH_CONCERN"]:
                res.update({"status": "HIGH_STRESS", "impact": "Generator load increases and equipment stress rises"})
                active_stress = True
                
        elif node == "fuel.reserve":
            fuel_days = state.get("fuel", {}).get("days_remaining", 999)
            if active_stress or fuel_days < CONFIG["FUEL_DAYS_LOW"]:
                res.update({"status": "DECLINING", "impact": "Fuel consumption increases, reserve margin decreases"})
                active_stress = True
                
        elif node == "logistics.resupply":
            fuel_days = state.get("fuel", {}).get("days_remaining", 999)
            if fuel_days < CONFIG["FUEL_DAYS_CRITICAL"]:
                res.update({"status": "CRITICAL_RISK", "impact": "Resupply window critically narrow"})
                active_stress = True
            elif active_stress or fuel_days < CONFIG["FUEL_DAYS_LOW"]:
                res.update({"status": "AT_RISK", "impact": "Resupply flexibility decreases"})
                active_stress = True
                
        elif node == "mission.continuity":
            if active_stress:
                res.update({"status": "ELEVATED_RISK", "impact": "Mission continuity risk increases"})
                
        return res, active_stress

    def _generate_recommendations(self, cascade: List[Dict[str, Any]], risk_level: str) -> List[str]:
        recs = []
        statuses = [step["status"] for step in cascade]
        
        if "HIGH_STRESS" in statuses and "energy.power" in [step["node"] for step in cascade]:
            recs.append("Consider reducing non-critical electrical load.")
        if "infrastructure.generator" in [step["node"] for step in cascade if step["status"] == "HIGH_STRESS"]:
            recs.append("Prioritize generator inspection/maintenance.")
        if "logistics.resupply" in [step["node"] for step in cascade if step["status"] in ["AT_RISK", "CRITICAL_RISK"]]:
            recs.append("Review resupply schedule and monitor fuel reserve closely.")
            
        if risk_level == "CRITICAL":
            recs.append("Immediate human review of station systems required.")
            
        return list(dict.fromkeys(recs)) # Deduplicate

    def evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main evaluation entrypoint.
        """
        station_id = state.get("station_id", "UNKNOWN")
        
        # 1. Risk Score
        risk_info = calculate_risk_score(state)
        
        # 2. Triggers
        triggers = self._identify_triggers(state)
        
        # 3. Cascade logic (Topological sort evaluation)
        cascade = []
        step_counter = 1
        active_stress = False # Tracks if stress is cascading down the chain
        
        # Evaluate nodes in order
        for node in self.graph.get_all_nodes():
            eval_res, active_stress = self._evaluate_node(node, state, active_stress)
            
            # Only include steps that are actually stressed/impacted in the final cascade output
            if eval_res["status"] != "NORMAL":
                eval_res["step"] = step_counter
                cascade.append(eval_res)
                step_counter += 1
                
        # 4. Recommendations
        recommendations = self._generate_recommendations(cascade, risk_info["risk_level"])
        
        return {
            "station_id": station_id,
            "overall_risk_score": risk_info["risk_score"],
            "risk_level": risk_info["risk_level"],
            "trigger_events": triggers,
            "cascade": cascade,
            "contributors": risk_info["contributors"],
            "recommendations": recommendations
        }

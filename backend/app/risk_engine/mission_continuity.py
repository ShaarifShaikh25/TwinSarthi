"""
Mission Continuity Engine for POLAR-TWIN
Calculates a unified, explainable 0-100 index for station operational margin.

IMPORTANT: Designed for synthetic/demo telemetry.
Scores and weights are PROTOTYPE assumptions, not official NCPOR operating limits.
"""
from typing import Dict, Any, List, Tuple, Optional

class MissionContinuityEngine:
    def __init__(self):
        # Prototype assumptions for SIH demonstration
        self.default_weights = {
            "energy": 0.25,
            "fuel": 0.20,
            "equipment": 0.20,
            "inventory": 0.15,
            "environment": 0.10,
            "communication": 0.10
        }
        
    def _score_energy(self, state: Dict[str, Any]) -> Optional[Tuple[float, List[str]]]:
        energy = state.get("energy")
        if not energy or "generator_load_percent" not in energy:
            return None
            
        load = energy["generator_load_percent"]
        reasons = []
        
        if load <= 50.0:
            score = 100.0
        elif load <= 70.0:
            score = 100.0 - ((load - 50.0) / 20.0) * 20.0
        elif load <= 85.0:
            score = 80.0 - ((load - 70.0) / 15.0) * 30.0
            reasons.append("Generator load is approaching a high-stress range.")
        elif load <= 95.0:
            score = 50.0 - ((load - 85.0) / 10.0) * 30.0
            reasons.append("Generator load is critically high.")
        else:
            score = max(0.0, 20.0 - ((load - 95.0) / 5.0) * 20.0)
            reasons.append("Generator load is beyond safe continuous limits.")
            
        return max(0.0, min(100.0, score)), reasons

    def _score_fuel(self, state: Dict[str, Any]) -> Optional[Tuple[float, List[str]]]:
        fuel = state.get("fuel")
        if not fuel:
            return None
            
        days = fuel.get("days_remaining")
        if days is None:
            level = fuel.get("fuel_level_liters")
            cons = fuel.get("fuel_consumption_lph")
            if level is not None and cons is not None:
                safe_cons = max(cons, 1e-6)
                days = level / (safe_cons * 24.0)
            else:
                return None
                
        reasons = []
        if days >= 14.0:
            score = 100.0
        elif days >= 7.0:
            score = 70.0 + ((days - 7.0) / 7.0) * 30.0
        elif days >= 3.0:
            score = 30.0 + ((days - 3.0) / 4.0) * 40.0
            reasons.append("Fuel reserve is below the preferred operational margin.")
        else:
            score = (max(0.0, days) / 3.0) * 30.0
            reasons.append("Fuel reserve is critically low.")
            
        return max(0.0, min(100.0, score)), reasons

    def _score_equipment(self, state: Dict[str, Any]) -> Optional[Tuple[float, List[str]]]:
        equip = state.get("equipment")
        if not equip:
            return None
            
        gen = equip.get("generator", {})
        hvac = equip.get("hvac", {})
        
        gen_h = gen.get("health_score")
        hvac_h = hvac.get("health_score")
        
        if gen_h is None and hvac_h is None:
            return None
            
        reasons = []
        
        if gen_h is not None and hvac_h is not None:
            # Generator is critical infrastructure, heavily weighted
            score = (gen_h * 0.7) + (hvac_h * 0.3)
            # Conservative clamping: if generator is failing, entire equipment continuity falls
            if gen_h < 40:
                score = min(score, gen_h)
                
            if gen_h < 60: reasons.append("Generator health is low.")
            if gen.get("degradation_trend") == "DEGRADING": reasons.append("Generator degradation trend is increasing.")
            if hvac_h < 60: reasons.append("HVAC health is low.")
            
        elif gen_h is not None:
            score = gen_h
            if gen_h < 60: reasons.append("Generator health is low.")
            if gen.get("degradation_trend") == "DEGRADING": reasons.append("Generator degradation trend is increasing.")
        else:
            score = hvac_h
            if hvac_h < 60: reasons.append("HVAC health is low.")
            if hvac.get("degradation_trend") == "DEGRADING": reasons.append("HVAC degradation trend is increasing.")
            
        return max(0.0, min(100.0, score)), reasons

    def _score_inventory(self, state: Dict[str, Any]) -> Optional[Tuple[float, List[str]]]:
        logistics = state.get("logistics")
        if not logistics:
            return None
            
        def _days_to_score(d):
            if d >= 30: return 100.0
            if d >= 15: return 80.0
            if d >= 7: return 50.0
            return 20.0
            
        scores = []
        if "food_days_remaining" in logistics: scores.append(_days_to_score(logistics["food_days_remaining"]))
        if "medicine_days_remaining" in logistics: scores.append(_days_to_score(logistics["medicine_days_remaining"]))
        if "spares_days_remaining" in logistics: scores.append(_days_to_score(logistics["spares_days_remaining"]))
        
        if not scores:
            return None
            
        score = sum(scores) / len(scores)
        reasons = []
        if score < 60:
            reasons.append("Inventory reserves are reduced.")
        if score < 40:
            reasons.append("Critical supplies are running low.")
            
        return score, reasons

    def _score_environment(self, state: Dict[str, Any]) -> Optional[Tuple[float, List[str]]]:
        env = state.get("environment")
        if not env:
            return None
            
        temp = env.get("temperature_c")
        wind = env.get("wind_speed_mps")
        
        if temp is None and wind is None:
            return None
            
        score = 100.0
        reasons = []
        
        if temp is not None:
            if temp < -30:
                score -= 40
                reasons.append("Severe cold temperature is stressing station systems.")
            elif temp < -15:
                score -= 20
                reasons.append("Low temperature is increasing environmental stress.")
                
        if wind is not None:
            if wind > 25:
                score -= 40
                reasons.append("Severe wind speed presents operational hazards.")
            elif wind > 15:
                score -= 20
                reasons.append("High wind is contributing to environmental stress.")
                
        # Optional Step 7 context integration
        risk_context = state.get("risk", {}).get("overall_risk_score", 0)
        if risk_context > 75:
            score -= 15
            reasons.append("Cascading risk engine indicates severe compounding environmental/operational threat.")
            
        return max(0.0, min(100.0, score)), reasons

    def _score_communication(self, state: Dict[str, Any]) -> Optional[Tuple[float, List[str]]]:
        comm = state.get("communication")
        if not comm or "status" not in comm:
            return None
            
        status = comm.get("status", "UNKNOWN").upper()
        avail = comm.get("availability", 1.0)
        
        reasons = []
        if status == "ONLINE":
            base = 100.0
        elif status == "DEGRADED":
            base = 50.0
            reasons.append("Communication link is degraded.")
        elif status == "OFFLINE":
            base = 0.0
            reasons.append("Communication link is offline.")
        else:
            base = 100.0 # UNKNOWN defaults to optimistic if we don't know
            
        score = base * avail
        if avail < 0.9 and status == "ONLINE":
            reasons.append("Communication availability is unstable.")
            
        return max(0.0, min(100.0, score)), reasons

    def _get_status_category(self, score: float) -> str:
        if score >= 80: return "STABLE"
        if score >= 60: return "WATCH"
        if score >= 40: return "AT_RISK"
        if score >= 20: return "SEVERE"
        return "CRITICAL"
        
    def _get_component_status(self, score: float) -> str:
        if score >= 80: return "GOOD"
        if score >= 60: return "REDUCED"
        if score >= 40: return "STRESSED"
        return "CRITICAL"

    def calculate_mission_continuity(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates unified Mission Continuity Score.
        Safely handles missing fields by renormalizing component weights.
        """
        components_calc = {
            "energy": self._score_energy(state),
            "fuel": self._score_fuel(state),
            "equipment": self._score_equipment(state),
            "inventory": self._score_inventory(state),
            "environment": self._score_environment(state),
            "communication": self._score_communication(state)
        }
        
        available = {}
        missing = []
        active_weight_sum = 0.0
        
        # Identify available vs missing components
        for name, result in components_calc.items():
            if result is not None:
                available[name] = result
                active_weight_sum += self.default_weights[name]
            else:
                missing.append(name)
                
        if active_weight_sum == 0:
            # Fallback if entirely empty
            return {
                "station_id": state.get("station_id", "UNKNOWN"),
                "mission_continuity_score": 0.0,
                "status": "UNKNOWN",
                "components": {},
                "key_risks": ["No operational telemetry available"],
                "recommendations": ["Restore telemetry systems immediately."],
                "data_quality": {"available_components": [], "missing_components": missing, "coverage": 0.0}
            }
            
        # Renormalize weights
        components_out = {}
        total_score = 0.0
        
        key_risks = []
        recommendations = []
        
        for name, (score, reasons) in available.items():
            renorm_weight = self.default_weights[name] / active_weight_sum
            contribution = score * renorm_weight
            total_score += contribution
            
            components_out[name] = {
                "score": round(score, 2),
                "weight": round(renorm_weight, 4),
                "weighted_contribution": round(contribution, 2),
                "status": self._get_component_status(score),
                "reasons": reasons
            }
            
            # Key risks & Recommendations
            if score < 40:
                if name == "fuel":
                    key_risks.append("Low fuel reserve")
                    recommendations.append("Monitor fuel reserve and review resupply margin.")
                elif name == "equipment":
                    key_risks.append("Critical equipment health concern")
                    recommendations.append("Prioritize generator inspection/maintenance.")
                elif name == "energy":
                    key_risks.append("Severe energy stress")
                    recommendations.append("Consider reducing non-critical electrical load.")
                elif name == "environment":
                    key_risks.append("Severe environmental stress")
                    recommendations.append("Halt external operations and preserve heat.")
                elif name == "inventory":
                    key_risks.append("Critical inventory shortage")
                    recommendations.append("Review resupply priorities for critical inventory.")
                elif name == "communication":
                    key_risks.append("Communication availability is low")
                    recommendations.append("Review communication link availability and local fallback procedures.")
                    
        # Remove duplicates
        recommendations = list(dict.fromkeys(recommendations))
        
        return {
            "station_id": state.get("station_id", "UNKNOWN"),
            "mission_continuity_score": round(total_score, 2),
            "status": self._get_status_category(total_score),
            "components": components_out,
            "key_risks": key_risks,
            "recommendations": recommendations,
            "data_quality": {
                "available_components": list(available.keys()),
                "missing_components": missing,
                "coverage": round(active_weight_sum, 2)
            }
        }

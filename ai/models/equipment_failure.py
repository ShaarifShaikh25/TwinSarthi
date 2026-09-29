"""
Equipment Failure Predictor
Unified POLAR-TWIN equipment health/failure-risk interface.
Uses heuristic rules, trend analysis, and Step 5 anomaly scores to assess degradation.

IMPORTANT: Designed for synthetic/demo telemetry.
Thresholds are PROTOTYPE assumptions, not official NCPOR operating limits.
This complements the existing generator-specific ML models in facility_predictive_maintenance/.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class EquipmentFailurePredictor:
    def __init__(self, equipment_type: str = "GENERATOR"):
        self.equipment_type = equipment_type.upper()
        if self.equipment_type not in ["GENERATOR", "HVAC"]:
            raise ValueError("Supported equipment types: GENERATOR, HVAC")
            
        self.criticality = "HIGH" if self.equipment_type == "GENERATOR" else "MEDIUM"
        
        # PROTOTYPE CONFIGURATION THRESHOLDS
        self.config = {
            "GENERATOR": {
                "weights": {
                    "load_stress": 0.30,
                    "trend_stress": 0.25,
                    "anomaly_stress": 0.25,
                    "runtime_stress": 0.20
                },
                "high_load_threshold": 80.0,
                "max_runtime_threshold": 5000.0
            },
            "HVAC": {
                "weights": {
                    "efficiency_stress": 0.40,
                    "trend_stress": 0.30,
                    "anomaly_stress": 0.30
                }
            }
        }
        
        self.baseline_stats = {}
        
    def fit(self, df: pd.DataFrame):
        """
        Calibrates baseline prototype statistics for failure-risk logic.
        (e.g., establishing normal efficiency ratios).
        """
        df = df.copy()
        if self.equipment_type == "HVAC":
            if "hvac_load_kw" in df.columns and "temperature_c" in df.columns:
                # Approximate typical ratio of HVAC load per degree below 0
                temp_drop = np.maximum(0, -df["temperature_c"])
                ratio = df["hvac_load_kw"] / (temp_drop + 1.0)
                self.baseline_stats["hvac_temp_ratio_median"] = ratio.median()
                self.baseline_stats["hvac_temp_ratio_mad"] = np.median(np.abs(ratio - ratio.median()))
                
        elif self.equipment_type == "GENERATOR":
            if "fuel_consumption_lph" in df.columns and "generator_load_percent" in df.columns:
                safe_load = np.maximum(df["generator_load_percent"], 1.0)
                ratio = df["fuel_consumption_lph"] / safe_load
                self.baseline_stats["fuel_load_ratio_median"] = ratio.median()
                self.baseline_stats["fuel_load_ratio_mad"] = np.median(np.abs(ratio - ratio.median()))

    def _calculate_degradation_trend(self, row: pd.Series) -> str:
        """Evaluates trend based on current vs rolling historical means."""
        if self.equipment_type == "GENERATOR":
            if "generator_load_percent" in row and "generator_load_percent_rolling_mean_6" in row:
                curr = row["generator_load_percent"]
                roll = row["generator_load_percent_rolling_mean_6"]
                # 5% relative increase threshold
                if curr > roll * 1.05: return "DEGRADING"
                if curr < roll * 0.95: return "IMPROVING"
        elif self.equipment_type == "HVAC":
            if "hvac_load_kw" in row and "power_consumption_kw_rolling_mean_6" in row:
                # We use power consumption rolling as proxy for total station demand trend
                curr = row["hvac_load_kw"]
                roll = row["power_consumption_kw_rolling_mean_6"] * 0.4 # Assuming ~40% base HVAC ratio
                if curr > roll * 1.10: return "DEGRADING"
                if curr < roll * 0.90: return "IMPROVING"
        
        return "STABLE"

    def _calculate_risk_components(self, row: pd.Series) -> Dict[str, float]:
        """Calculates individual stress factors between [0, 1]."""
        components = {}
        
        # 1. Anomaly Stress (if Step 5 info is passed in)
        anomaly_score = row.get("anomaly_score", 0.0)
        components["anomaly_stress"] = np.clip(anomaly_score, 0.0, 1.0)
        
        # 2. Trend Stress
        trend = self._calculate_degradation_trend(row)
        components["trend_stress"] = 1.0 if trend == "DEGRADING" else (0.5 if trend == "STABLE" else 0.0)
        
        if self.equipment_type == "GENERATOR":
            # Load stress
            load = row.get("generator_load_percent", 0.0)
            threshold = self.config["GENERATOR"]["high_load_threshold"]
            components["load_stress"] = np.clip((load - threshold) / (100 - threshold), 0.0, 1.0) if load > threshold else 0.0
            
            # Runtime stress
            runtime = row.get("runtime_hours", 0.0)
            max_rt = self.config["GENERATOR"]["max_runtime_threshold"]
            components["runtime_stress"] = np.clip(runtime / max_rt, 0.0, 1.0)
            
        elif self.equipment_type == "HVAC":
            # Efficiency stress: Is HVAC drawing too much for the current temp?
            load = row.get("hvac_load_kw", 0.0)
            temp = row.get("temperature_c", 0.0)
            temp_drop = max(0, -temp)
            current_ratio = load / (temp_drop + 1.0)
            
            base_ratio = self.baseline_stats.get("hvac_temp_ratio_median", current_ratio)
            mad = self.baseline_stats.get("hvac_temp_ratio_mad", 1.0)
            
            z_score = (current_ratio - base_ratio) / (mad + 1e-6)
            components["efficiency_stress"] = np.clip(z_score / 3.0, 0.0, 1.0) if z_score > 0 else 0.0
            
        return components

    def _generate_risk_factors(self, components: Dict[str, float], row: pd.Series) -> List[str]:
        """Translates high stress components into human-readable risk factors."""
        factors = []
        if components.get("anomaly_stress", 0) > 0.5:
            factors.append("Repeated abnormal operating signals detected (Step 5 Anomaly)")
            
        if components.get("trend_stress", 0) > 0.8:
            factors.append(f"{self.equipment_type} load trend is increasing/degrading")
            
        if self.equipment_type == "GENERATOR":
            if components.get("load_stress", 0) > 0.5:
                factors.append("Generator load is experiencing high operational stress")
            if components.get("runtime_stress", 0) > 0.8:
                factors.append("Equipment runtime hours approaching maintenance threshold")
        
        elif self.equipment_type == "HVAC":
            if components.get("efficiency_stress", 0) > 0.5:
                factors.append("HVAC demand is unusually high relative to environmental temperature")
                
        return factors

    def calculate_failure_risk(self, row: pd.Series) -> float:
        """Returns bounded risk score [0, 1] using configurable weighted prototype assumptions."""
        comps = self._calculate_risk_components(row)
        weights = self.config[self.equipment_type]["weights"]
        
        risk = 0.0
        for key, weight in weights.items():
            risk += comps.get(key, 0.0) * weight
            
        return float(np.clip(risk, 0.0, 1.0))

    def calculate_health_score(self, risk_score: float) -> float:
        """Inverts risk score into a health score [0, 100]."""
        return round((1.0 - risk_score) * 100.0, 2)

    def get_maintenance_priority(self, health_score: float, trend: str) -> str:
        """
        Derives priority tier. Prototype UI categories, NOT official policy.
        """
        if health_score < 40: return "CRITICAL"
        if health_score < 60: return "HIGH"
        if health_score < 80: return "MEDIUM"
        
        # Even if healthy, degrading trend bumps priority slightly
        if trend == "DEGRADING" and health_score < 90:
            return "MEDIUM"
            
        return "LOW"

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Main interface mapping telemetry rows to equipment health states."""
        results = []
        for i, row in df.iterrows():
            trend = self._calculate_degradation_trend(row)
            comps = self._calculate_risk_components(row)
            risk_score = self.calculate_failure_risk(row)
            health = self.calculate_health_score(risk_score)
            priority = self.get_maintenance_priority(health, trend)
            factors = self._generate_risk_factors(comps, row)
            
            # Derived Status string based on health
            if health >= 80: status = "HEALTHY"
            elif health >= 60: status = "MONITOR"
            elif health >= 40: status = "MAINTENANCE_RECOMMENDED"
            else: status = "HIGH_RISK"
            
            # Use index or station ID as a fake equipment ID for the prototype
            eq_id = f"{self.equipment_type}_{row.get('station_id', '01')}"
            
            results.append({
                "equipment_id": eq_id,
                "equipment_type": self.equipment_type,
                "health_score": health,
                "failure_risk_score": round(risk_score, 4),
                "degradation_trend": trend,
                "status": status,
                "maintenance_priority": priority,
                "risk_factors": factors
            })
            
        return results

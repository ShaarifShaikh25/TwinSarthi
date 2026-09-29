"""
Anomaly Detector Model
Station-wide multi-signal anomaly detection layer for POLAR-TWIN.
Uses Isolation Forest to detect abnormal operational patterns.

IMPORTANT: Designed for synthetic/demo telemetry.
This complements, but does NOT replace, the existing generator-specific ML models.
"""
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List, Optional

class AnomalyDetector:
    def __init__(self, random_state: int = 42, contamination: str = "auto"):
        self.model = IsolationForest(n_estimators=200, contamination=contamination, random_state=random_state)
        self.features = []
        self.baseline_stats = {}
        self.severity_thresholds = {
            "NORMAL": 0.25,
            "LOW": 0.50,
            "MEDIUM": 0.75,
            "HIGH": 1.00
        }
        
    def fit(self, X: pd.DataFrame):
        """Fits the Isolation Forest and computes baseline median/MAD for explanations."""
        self.features = list(X.columns)
        self.model.fit(X)
        
        # Compute robust baseline statistics for explainability
        for col in self.features:
            median_val = X[col].median()
            mad_val = np.median(np.abs(X[col] - median_val))
            self.baseline_stats[col] = {
                "median": median_val,
                "mad": mad_val
            }
            
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Returns boolean array indicating ML anomalies (True = Anomaly)."""
        # IsolationForest returns -1 for outliers and 1 for inliers.
        preds = self.model.predict(X[self.features])
        return preds == -1
        
    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Calculates normalized anomaly score [0.0 - 1.0].
         decision_function: >0 is normal, <0 is anomalous. (typically ranges ~ -0.5 to 0.5)
         We map this safely to 0-1 range.
        """
        raw_scores = self.model.decision_function(X[self.features])
        # Map: 0.5 -> 0.0 (Normal), 0.0 -> 0.5 (Medium), -0.5 -> 1.0 (High)
        normalized = 0.5 - raw_scores
        return np.clip(normalized, 0.0, 1.0)
        
    def _get_severity(self, score_val: float) -> str:
        """Translates normalized score into categorical severity."""
        if score_val <= self.severity_thresholds["NORMAL"]: return "NORMAL"
        if score_val <= self.severity_thresholds["LOW"]: return "LOW"
        if score_val <= self.severity_thresholds["MEDIUM"]: return "MEDIUM"
        return "HIGH"

    def _check_physical_anomaly(self, row: pd.Series) -> List[str]:
        """Performs domain/physics sanity checks."""
        reasons = []
        if "generator_load_percent" in row and row["generator_load_percent"] > 100:
            reasons.append("generator_load_percent exceeds 100% (Physical Limit)")
        if "power_consumption_kw" in row and row["power_consumption_kw"] < 0:
            reasons.append("power_consumption_kw is negative (Physical Limit)")
        if "fuel_consumption_lph" in row and row["fuel_consumption_lph"] < 0:
            reasons.append("fuel_consumption_lph is negative (Physical Limit)")
        if "fuel_level_liters" in row and row["fuel_level_liters"] < 0:
            reasons.append("fuel_level_liters is negative (Physical Limit)")
        if "humidity_percent" in row and (row["humidity_percent"] < 0 or row["humidity_percent"] > 100):
            reasons.append("humidity_percent outside 0-100 range (Physical Limit)")
        return reasons

    def explain(self, row: pd.Series) -> List[str]:
        """Generates human-readable explanations based on robust MAD deviation."""
        reasons = []
        
        # Check domain physics first
        physics_reasons = self._check_physical_anomaly(row)
        reasons.extend(physics_reasons)
        
        # Explain ML deviations
        contributions = self.get_signal_contribution(pd.DataFrame([row]))[0]
        
        for feature, deviation in contributions.items():
            if deviation > 3.0:
                reasons.append(f"{feature} is significantly above baseline")
            elif deviation < -3.0:
                reasons.append(f"{feature} is significantly below baseline")
                
        return reasons

    def get_signal_contribution(self, X: pd.DataFrame) -> List[Dict[str, float]]:
        """
        Returns robust z-scores (deviations) for each feature.
        Heuristic contribution based on deviation, NOT native isolation forest importance.
        """
        contributions = []
        for _, row in X[self.features].iterrows():
            row_contrib = {}
            for col in self.features:
                val = row[col]
                base_median = self.baseline_stats[col]["median"]
                base_mad = self.baseline_stats[col]["mad"]
                
                # Robust deviation
                z_score = (val - base_median) / (base_mad + 1e-6)
                row_contrib[col] = round(float(z_score), 2)
            # Sort by absolute deviation descending
            row_contrib = {k: v for k, v in sorted(row_contrib.items(), key=lambda item: abs(item[1]), reverse=True)}
            contributions.append(row_contrib)
        return contributions

    def detect(self, X: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Main detection interface.
        Returns a list of structured anomaly outputs for each row.
        """
        is_anom_array = self.predict(X)
        scores_array = self.score(X)
        
        results = []
        for i, (_, row) in enumerate(X.iterrows()):
            ml_is_anom = bool(is_anom_array[i])
            score = float(scores_array[i])
            
            # Physics checks
            physics_reasons = self._check_physical_anomaly(row)
            has_physics_anom = len(physics_reasons) > 0
            
            # Final anomaly status
            final_is_anom = ml_is_anom or has_physics_anom
            
            if has_physics_anom and score < 0.75:
                # Force high score if physically impossible
                score = 0.95
                
            severity = self._get_severity(score)
            
            reasons = []
            if final_is_anom:
                reasons = self.explain(row)
                if not reasons:
                    reasons.append("Unusual multivariate pattern detected without extreme single-feature deviation.")
            
            results.append({
                "is_anomaly": final_is_anom,
                "has_physical_anomaly": has_physics_anom,
                "anomaly_score": round(score, 4),
                "severity": severity,
                "reasons": reasons
            })
            
        return results

    def save(self, filepath: str):
        """Persists model to disk via joblib."""
        state = {
            "model": self.model,
            "features": self.features,
            "baseline_stats": self.baseline_stats,
            "severity_thresholds": self.severity_thresholds
        }
        joblib.dump(state, filepath)
        
    @classmethod
    def load(cls, filepath: str) -> "AnomalyDetector":
        """Loads model from disk via joblib."""
        state = joblib.load(filepath)
        instance = cls()
        instance.model = state["model"]
        instance.features = state["features"]
        instance.baseline_stats = state["baseline_stats"]
        instance.severity_thresholds = state["severity_thresholds"]
        return instance

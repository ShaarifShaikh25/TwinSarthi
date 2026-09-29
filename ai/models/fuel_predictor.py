"""
Fuel Predictor Model
Predicts future fuel consumption (lph) and projects derived fuel levels and days remaining.

IMPORTANT: Designed for synthetic/demo telemetry.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Dict, Any, List

class FuelPredictor:
    def __init__(self, random_state: int = 42):
        self.model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=random_state)
        self.features = []
        
    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Fits the fuel consumption model."""
        self.features = list(X.columns)
        self.model.fit(X, y)
        
    def predict_consumption(self, X: pd.DataFrame) -> np.ndarray:
        """Predicts fuel consumption rate (L/h), bounded to >= 0."""
        preds = self.model.predict(X[self.features])
        return np.maximum(preds, 0.0)
        
    def predict_fuel_level(self, X: pd.DataFrame, current_fuel_level: pd.Series, forecast_hours: float) -> np.ndarray:
        """Derives projected fuel level after forecast_hours based on predicted consumption."""
        consumption_lph = self.predict_consumption(X)
        future_fuel = current_fuel_level.values - (consumption_lph * forecast_hours)
        return np.maximum(future_fuel, 0.0)
        
    def predict_days_remaining(self, X: pd.DataFrame, current_fuel_level: pd.Series) -> np.ndarray:
        """Derives estimated days of fuel remaining based on predicted current consumption."""
        consumption_lph = self.predict_consumption(X)
        # Avoid division by zero by setting a tiny minimum threshold
        safe_consumption_lpd = np.maximum(consumption_lph * 24.0, 1e-6)
        days = current_fuel_level.values / safe_consumption_lpd
        return days
        
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Evaluates fuel consumption model performance on synthetic/demo telemetry."""
        preds = self.predict_consumption(X)
        return {
            "mae": mean_absolute_error(y, preds),
            "rmse": np.sqrt(mean_squared_error(y, preds)),
            "r2": r2_score(y, preds)
        }
        
    def get_feature_importance(self) -> Dict[str, float]:
        """Returns feature importance mapping for explainability."""
        if not self.features:
            return {}
        importances = self.model.feature_importances_
        feat_imp = sorted(zip(self.features, importances), key=lambda x: x[1], reverse=True)
        return {k: round(float(v), 4) for k, v in feat_imp}

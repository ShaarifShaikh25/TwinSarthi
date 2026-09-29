"""
Energy Forecaster Model
Predicts future power consumption based on current and historical environmental/operational features.

IMPORTANT: Designed for synthetic/demo telemetry.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Dict, Any, List

class EnergyForecaster:
    def __init__(self, random_state: int = 42):
        self.model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=random_state)
        self.features = []
        
    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Fits the energy forecasting model."""
        self.features = list(X.columns)
        self.model.fit(X, y)
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predicts future power consumption, strictly bounded to >= 0."""
        preds = self.model.predict(X[self.features])
        return np.maximum(preds, 0.0)
        
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Evaluates model performance on synthetic/demo telemetry."""
        preds = self.predict(X)
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

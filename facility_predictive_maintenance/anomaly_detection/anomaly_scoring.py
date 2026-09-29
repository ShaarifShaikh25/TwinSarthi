"""
Anomaly Scoring Module
Project: POLAR-TWIN — Facility Predictive Maintenance
Asset: Diesel Generator

Transforms raw Isolation Forest decision_function output into a normalized
0.0 (normal) to 1.0 (highly anomalous) score.

The raw IF decision_function returns negative values for anomalies and positive
for normal points. We invert and normalize using training distribution percentiles
for robustness.

Thresholds are MODEL CONFIGURATION / SIMULATION ASSUMPTIONS,
not official NCPOR operational thresholds.
"""
import numpy as np
from typing import Tuple, List, Dict, Optional

# --- RISK LEVEL CONFIGURATION ---
# These are SIMULATION ASSUMPTIONS, not official NCPOR thresholds.
DEFAULT_RISK_THRESHOLDS = {
    "NORMAL": (0.0, 0.25),
    "LOW": (0.25, 0.45),
    "MEDIUM": (0.45, 0.65),
    "HIGH": (0.65, 0.85),
    "CRITICAL": (0.85, 1.0),
}


def fit_score_normalizer(
    raw_scores_train: np.ndarray,
) -> Tuple[float, float]:
    """
    Fit normalization parameters from the training distribution of raw
    Isolation Forest decision_function scores.

    We use the 2nd and 98th percentiles of the TRAINING distribution
    so that extreme outliers in future test data can still exceed 1.0
    before clipping, providing a robust mapping.

    Returns:
        (score_min, score_max) fitted on training data.
    """
    score_min = float(np.percentile(raw_scores_train, 2))
    score_max = float(np.percentile(raw_scores_train, 98))
    return score_min, score_max


def normalize_anomaly_scores(
    raw_scores: np.ndarray,
    score_min: float,
    score_max: float,
) -> np.ndarray:
    """
    Normalize raw IF decision_function scores to [0, 1].

    Raw IF scores: higher = more normal, lower/negative = more anomalous.
    We INVERT so that 1.0 = highly anomalous.

    Steps:
      1. Invert: inverted = -raw_score
      2. Scale using training-fitted min/max.
      3. Clip to [0, 1].
    """
    inverted = -raw_scores
    inv_min = -score_max  # inversion flips min/max
    inv_max = -score_min

    denom = inv_max - inv_min
    if denom == 0:
        return np.zeros_like(raw_scores)

    normalized = (inverted - inv_min) / denom
    return np.clip(normalized, 0.0, 1.0)


def assign_risk_level(
    anomaly_score: float,
    thresholds: Optional[Dict[str, Tuple[float, float]]] = None,
) -> str:
    """
    Map a normalized anomaly score to a risk level string.
    """
    if thresholds is None:
        thresholds = DEFAULT_RISK_THRESHOLDS
    for level, (low, high) in thresholds.items():
        if low <= anomaly_score < high:
            return level
    return "CRITICAL"  # anything >= 1.0


def assign_risk_levels_batch(
    anomaly_scores: np.ndarray,
    thresholds: Optional[Dict[str, Tuple[float, float]]] = None,
) -> List[str]:
    """
    Vectorized risk-level assignment for an array of scores.
    """
    return [assign_risk_level(float(s), thresholds) for s in anomaly_scores]

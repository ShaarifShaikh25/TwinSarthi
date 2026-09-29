"""
Explainability Module
Project: POLAR-TWIN — Facility Predictive Maintenance
Asset: Diesel Generator

Provides per-sample explanation of WHY the anomaly model flagged a reading.
Uses deviation from healthy training median, scaled by MAD (Median Absolute
Deviation), to rank contributing signals.

IMPORTANT: These are CONTRIBUTING SIGNALS, not proven mechanical causes.
Isolation Forest does not provide causal attribution.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

# --- Physical Domain Mapping ---
# Maps engineered features to their physical domain for evidence classification.
FEATURE_DOMAIN_MAP: Dict[str, str] = {
    "load_adjusted_fuel_deviation": "fuel",
    "fuel_efficiency_proxy": "fuel",
    "exhaust_temp_rolling_mean_15m": "thermal",
    "exhaust_temp_rate_c_per_min": "thermal",
    "exhaust_temp_dev_c": "thermal",
    "vibration_trend": "vibration",
    "vibration_rolling_mean_30m": "vibration",
    "combustion_signature_proxy": "cross_domain",
    "combustion_signature_rolling_1h": "cross_domain",
    "load_pct": "operating_context",
    "rpm": "operating_context",
    "coolant_temp_c": "thermal",
    "oil_pressure_bar": "operating_context",
}

# Contribution level thresholds (based on MAD-scaled deviation)
# These are SIMULATION ASSUMPTIONS.
CONTRIBUTION_THRESHOLDS = {
    "HIGH": 3.0,
    "MEDIUM": 2.0,
    "LOW": 1.0,
}


def fit_baseline_stats(
    X_train: pd.DataFrame,
) -> Tuple[pd.Series, pd.Series]:
    """
    Compute per-feature median and MAD from the healthy training set.
    MAD = median(|x_i - median(x)|)
    A MAD of 0 is replaced with a small epsilon to avoid division by zero.
    """
    medians = X_train.median()
    mad = (X_train - medians).abs().median()
    mad = mad.replace(0, 1e-6)  # avoid division by zero
    return medians, mad


def compute_feature_deviations(
    sample: pd.Series,
    medians: pd.Series,
    mad: pd.Series,
) -> pd.Series:
    """
    Compute MAD-scaled deviation for each feature in a single sample.
    deviation_i = |sample_i - median_i| / MAD_i
    """
    return ((sample - medians) / mad).abs()


def get_contribution_level(deviation: float) -> str:
    """
    Map a MAD-scaled deviation to a contribution level.
    """
    if deviation >= CONTRIBUTION_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif deviation >= CONTRIBUTION_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    elif deviation >= CONTRIBUTION_THRESHOLDS["LOW"]:
        return "LOW"
    return "NEGLIGIBLE"


def explain_anomaly(
    sample: pd.Series,
    medians: pd.Series,
    mad: pd.Series,
    top_n: int = 5,
) -> Dict:
    """
    For one anomalous sample, return ranked contributing signals,
    their domains, and the overall evidence pattern.

    Returns dict with:
      - contributing_signals: list of dicts with feature, deviation, contribution, domain, interpretation
      - evidence_pattern: SINGLE_SIGNAL | MULTI_SIGNAL | CROSS_DOMAIN
      - supporting_domains: list of unique physical domains with at least MEDIUM contribution
    """
    deviations = compute_feature_deviations(sample, medians, mad)
    ranked = deviations.sort_values(ascending=False).head(top_n)

    signals = []
    contributing_domains = set()
    for feat, dev in ranked.items():
        level = get_contribution_level(dev)
        domain = FEATURE_DOMAIN_MAP.get(feat, "unknown")
        if level in ("HIGH", "MEDIUM"):
            contributing_domains.add(domain)
        signals.append({
            "feature": feat,
            "deviation": round(float(dev), 2),
            "contribution": level,
            "domain": domain,
            "interpretation": "CONTRIBUTING SIGNAL",
        })

    # Classify evidence pattern
    # Remove cross_domain and operating_context from domain count for pattern classification
    physical_domains = contributing_domains - {"cross_domain", "operating_context"}
    if len(physical_domains) >= 3:
        pattern = "CROSS_DOMAIN"
    elif len(physical_domains) >= 2:
        pattern = "MULTI_SIGNAL"
    elif len(physical_domains) == 1:
        pattern = "SINGLE_SIGNAL"
    else:
        pattern = "INSUFFICIENT_EVIDENCE"

    return {
        "contributing_signals": signals,
        "evidence_pattern": pattern,
        "supporting_domains": sorted(list(contributing_domains)),
    }

"""
Signal Contribution Analysis Module
Project: POLAR-TWIN — Facility Predictive Maintenance
Phase: 5.2

Extracts physical evidence from fundamental telemetry signals during an anomaly event.
Calculates robust deviations against the healthy training baseline (MAD).
Does NOT infer physical root causes, only extracts and ranks contributing signals.

All data must be considered SYNTHETIC_DATA for SIH 2026 demonstration.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any

# --- SIMULATION / ENGINEERING CONFIGURATION ---
# Not official NCPOR operational thresholds.
MAD_FLOOR = 1e-6
EVIDENCE_THRESHOLD_MAD = 2.0

# Evidence strength calculation weights
WEIGHT_MEAN_DEV = 0.4
WEIGHT_PEAK_DEV = 0.3
WEIGHT_PERSISTENCE = 0.3

# Normalization constants (assumed typical max dev to cap at 1.0)
MAX_EXPECTED_MAD_DEV = 10.0

# Fundamental signals for independent evidence scoring
FUNDAMENTAL_SIGNALS = [
    'load_adjusted_fuel_deviation',
    'fuel_efficiency_proxy',
    'exhaust_temp_dev_c',
    'exhaust_temp_rate_c_per_min',
    'vibration_trend',
    'vibration_mm_s',
    'load_pct',
    'rpm',
    'coolant_temp_c',
    'oil_pressure_bar'
]

# We deliberately EXCLUDE composites like combustion_signature_proxy from independent evidence scoring
# to prevent double counting underlying deviations in fuel, thermal, and mechanical domains.
COMPOSITE_SIGNALS = [
    'combustion_signature_proxy',
    'combustion_signature_rolling_1h'
]

DOMAIN_MAP = {
    'load_adjusted_fuel_deviation': 'FUEL_DOMAIN',
    'fuel_efficiency_proxy': 'FUEL_DOMAIN',
    'exhaust_temp_dev_c': 'THERMAL_DOMAIN',
    'exhaust_temp_rate_c_per_min': 'THERMAL_DOMAIN',
    'vibration_trend': 'MECHANICAL_DOMAIN',
    'vibration_mm_s': 'MECHANICAL_DOMAIN',
    'load_pct': 'OPERATING_CONTEXT',
    'rpm': 'OPERATING_CONTEXT',
    'coolant_temp_c': 'OPERATING_CONTEXT',
    'oil_pressure_bar': 'OPERATING_CONTEXT'
}


def calculate_evidence_strength(
    mean_dev: float,
    peak_dev: float,
    evidence_fraction: float
) -> float:
    """
    Calculate a simple 0.0 - 1.0 evidence strength score.
    This is NOT a failure probability or diagnostic certainty. 
    It is a heuristic for ranking evidence severity (SIMULATION ASSUMPTION).
    """
    # Normalize deviations to [0, 1] based on an expected maximum
    norm_mean = min(mean_dev / MAX_EXPECTED_MAD_DEV, 1.0)
    norm_peak = min(peak_dev / MAX_EXPECTED_MAD_DEV, 1.0)
    
    strength = (
        (norm_mean * WEIGHT_MEAN_DEV) +
        (norm_peak * WEIGHT_PEAK_DEV) +
        (evidence_fraction * WEIGHT_PERSISTENCE)
    )
    return round(float(np.clip(strength, 0.0, 1.0)), 4)


def analyze_event_signals(
    event_df: pd.DataFrame,
    baseline_medians: pd.Series,
    baseline_mad: pd.Series
) -> Dict[str, Any]:
    """
    Analyze fundamental signal contributions over an anomaly event window.
    Takes a dataframe representing an event window, along with healthy baseline stats.
    
    Returns structured JSON-ready dictionary ranking signal deviations.
    """
    result = {
        "data_type": "SYNTHETIC_DATA",
        "analysis_type": "SIGNAL_CONTRIBUTION",
        "event_status": "ANALYZED",
        "signals": [],
        "domain_summary": {}
    }
    
    if len(event_df) == 0:
        result["event_status"] = "EMPTY_EVENT"
        return result
        
    # Communication Gap Protection
    # Exclude samples with data_quality_warning == True from mechanical evidence logic
    if 'data_quality_warning' in event_df.columns:
        valid_mask = ~event_df['data_quality_warning'].astype(bool)
    else:
        valid_mask = pd.Series([True] * len(event_df), index=event_df.index)
    
    if valid_mask.sum() == 0:
        result["event_status"] = "INSUFFICIENT_TELEMETRY"
        return result

    valid_df = event_df[valid_mask]
    signals_analyzed = []
    
    for sig in FUNDAMENTAL_SIGNALS:
        if sig not in valid_df.columns:
            signals_analyzed.append({
                "signal": sig,
                "domain": DOMAIN_MAP.get(sig, "UNKNOWN"),
                "available": False,
                "evidence_status": "UNAVAILABLE"
            })
            continue
            
        series = valid_df[sig].dropna()
        if len(series) == 0:
            signals_analyzed.append({
                "signal": sig,
                "domain": DOMAIN_MAP.get(sig, "UNKNOWN"),
                "available": False,
                "evidence_status": "UNAVAILABLE"
            })
            continue
            
        # Robust MAD deviation calculation
        median = float(baseline_medians.get(sig, 0.0))
        mad = float(baseline_mad.get(sig, MAD_FLOOR))
        effective_mad = max(mad, MAD_FLOOR)
        
        abs_devs = (series - median).abs()
        robust_devs = abs_devs / effective_mad
        
        mean_dev = float(robust_devs.mean())
        peak_dev = float(robust_devs.max())
        max_abs = float(abs_devs.max())
        
        evidence_mask = robust_devs >= EVIDENCE_THRESHOLD_MAD
        evidence_samples = int(evidence_mask.sum())
        available_samples = len(series)
        evidence_fraction = evidence_samples / available_samples if available_samples > 0 else 0.0
        
        evidence_status = "EVIDENCE_POSITIVE" if evidence_fraction > 0 else "NOT_EVIDENCE_POSITIVE"
        
        strength = calculate_evidence_strength(mean_dev, peak_dev, evidence_fraction)
        
        signals_analyzed.append({
            "signal": sig,
            "domain": DOMAIN_MAP.get(sig, "UNKNOWN"),
            "available": True,
            "mean_deviation": round(mean_dev, 4),
            "peak_deviation": round(peak_dev, 4),
            "max_absolute_deviation": round(max_abs, 4),
            "evidence_fraction": round(evidence_fraction, 4),
            "available_samples": available_samples,
            "evidence_samples": evidence_samples,
            "evidence_status": evidence_status,
            "evidence_strength": strength
        })
        
    # Signal Ranking: Rank by evidence strength, then fraction, then peak
    signals_analyzed.sort(key=lambda x: (
        x.get("evidence_strength", 0.0), 
        x.get("evidence_fraction", 0.0), 
        x.get("peak_deviation", 0.0)
    ), reverse=True)
    
    result["signals"] = signals_analyzed
    
    # Domain Summary
    domain_summary = {}
    for sig_info in signals_analyzed:
        if not sig_info.get("available", False):
            continue
            
        d = sig_info["domain"]
        if d not in domain_summary:
            domain_summary[d] = {
                "evidence_signals": 0,
                "max_evidence_strength": 0.0
            }
            
        if sig_info["evidence_status"] == "EVIDENCE_POSITIVE":
            domain_summary[d]["evidence_signals"] += 1
            
        if sig_info["evidence_strength"] > domain_summary[d]["max_evidence_strength"]:
            domain_summary[d]["max_evidence_strength"] = sig_info["evidence_strength"]
            
    result["domain_summary"] = domain_summary
    
    return result

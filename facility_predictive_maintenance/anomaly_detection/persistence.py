"""
Temporal Persistence Module
Project: POLAR-TWIN — Facility Predictive Maintenance
Asset: Diesel Generator

Prevents single-point false alarms by requiring anomalies to persist
over a configurable time window before escalating.

Uses hysteresis with separate anomaly and recovery thresholds to prevent
event flickering around a single boundary.

All thresholds are MODEL CONFIGURATION / SIMULATION ASSUMPTIONS.
"""
import pandas as pd
import numpy as np
from typing import List

# --- PERSISTENCE CONFIGURATION ---
# SIMULATION ASSUMPTIONS — not official NCPOR thresholds.
# Calibrated against healthy-data validation score distribution:
#   Normal data: mean≈0.21, occasional noise peaks to ~0.80.
#   Combustion degradation data: sustained scores above 0.90.
#   Anomaly threshold at 0.85 passes only genuinely anomalous patterns.
#   Recovery at 0.65 provides wide hysteresis buffer.
#   Persistence window of 15 minutes filters transient noise spikes.
DEFAULT_ANOMALY_THRESHOLD = 0.85
DEFAULT_RECOVERY_THRESHOLD = 0.65
DEFAULT_PERSISTENCE_WINDOW = 15  # minutes


def apply_persistence(
    anomaly_scores: np.ndarray,
    anomaly_threshold: float = DEFAULT_ANOMALY_THRESHOLD,
    recovery_threshold: float = DEFAULT_RECOVERY_THRESHOLD,
    persistence_window: int = DEFAULT_PERSISTENCE_WINDOW,
) -> List[str]:
    """
    Apply temporal persistence with hysteresis.

    Logic:
      - A point enters ANOMALY state when score >= anomaly_threshold.
      - It remains in ANOMALY state until score drops below recovery_threshold
        for at least persistence_window consecutive points.
      - Consecutive anomaly points shorter than persistence_window are TRANSIENT.
      - Consecutive anomaly points >= persistence_window are PERSISTENT.

    Returns list of states: 'NORMAL', 'TRANSIENT', or 'PERSISTENT' per sample.
    """
    n = len(anomaly_scores)
    states: List[str] = ['NORMAL'] * n

    in_anomaly = False
    anomaly_run_length = 0
    recovery_run_length = 0

    for i in range(n):
        score = anomaly_scores[i]

        if not in_anomaly:
            # Check if we enter anomaly state
            if score >= anomaly_threshold:
                in_anomaly = True
                anomaly_run_length = 1
                recovery_run_length = 0
                states[i] = 'TRANSIENT'
            else:
                states[i] = 'NORMAL'
        else:
            # Currently in anomaly state
            if score >= recovery_threshold:
                # Still anomalous (or in hysteresis band)
                recovery_run_length = 0
                anomaly_run_length += 1
                if anomaly_run_length >= persistence_window:
                    states[i] = 'PERSISTENT'
                    # Also retroactively upgrade earlier TRANSIENT points in this run
                    for j in range(max(0, i - anomaly_run_length + 1), i):
                        if states[j] == 'TRANSIENT':
                            states[j] = 'PERSISTENT'
                else:
                    states[i] = 'TRANSIENT'
            else:
                # Score dropped below recovery threshold
                recovery_run_length += 1
                if recovery_run_length >= persistence_window:
                    # Recovery confirmed — exit anomaly state
                    in_anomaly = False
                    anomaly_run_length = 0
                    states[i] = 'NORMAL'
                else:
                    # Still in hysteresis zone
                    anomaly_run_length += 1
                    states[i] = 'TRANSIENT'

    return states

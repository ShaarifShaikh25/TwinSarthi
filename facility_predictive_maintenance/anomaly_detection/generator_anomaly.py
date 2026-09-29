"""
Generator Anomaly Detection Orchestrator
Project: POLAR-TWIN — Facility Predictive Maintenance
Asset: Diesel Generator

Runs the full Maintenance Intelligence Chain:
  Raw Features → ML Preprocessing → Isolation Forest → Score Normalization
  → Evidence Extraction → Communication-Gap Logic → Temporal Persistence
  → Event Grouping → Structured Output

All results are labeled SYNTHETIC_DATA.
Anomaly scores represent degree of unusualness, NOT probability of failure.
Contributing signals are evidence of unusual behavior, NOT proven causes.
"""
import pandas as pd
import numpy as np
import json
import joblib
import logging
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# --- FEATURE CONFIGURATION ---
# Explicitly separates model features, decision context, and ground truth.
# Ground truth fields are NEVER used as model inputs.

MODEL_FEATURES = [
    'load_adjusted_fuel_deviation',
    'fuel_efficiency_proxy',
    'exhaust_temp_rolling_mean_15m',
    'exhaust_temp_rate_c_per_min',
    'exhaust_temp_dev_c',
    'vibration_trend',
    'vibration_rolling_mean_30m',
    'combustion_signature_proxy',
    'combustion_signature_rolling_1h',
    'load_pct',
    'rpm',
    'coolant_temp_c',
    'oil_pressure_bar',
]

DECISION_CONTEXT_FIELDS = [
    'communication_gap_flag',
]

GROUND_TRUTH_FIELDS = [
    'anomaly_label',
    'anomaly_type',
]


def load_model_artifacts(model_dir: Path) -> Dict:
    """
    Load trained Isolation Forest, scaler, score normalizer params,
    and baseline stats from disk.
    """
    artifacts = {
        'model': joblib.load(model_dir / 'isolation_forest.joblib'),
        'scaler': joblib.load(model_dir / 'scaler.joblib'),
        'baseline_medians': joblib.load(model_dir / 'baseline_medians.joblib'),
        'baseline_mad': joblib.load(model_dir / 'baseline_mad.joblib'),
    }
    with open(model_dir / 'score_config.json', 'r') as f:
        artifacts['score_config'] = json.load(f)
    with open(model_dir / 'feature_config.json', 'r') as f:
        artifacts['feature_config'] = json.load(f)
    return artifacts


def run_generator_anomaly_detection(
    df: pd.DataFrame,
    model_dir: Path,
    asset_id: str = 'DG-01',
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Full anomaly detection pipeline for a generator features dataset.

    Args:
        df: DataFrame with Phase 3 features (including ground truth and context columns).
        model_dir: Path to saved model artifacts.
        asset_id: Identifier for the generator.

    Returns:
        (results_df, events_list)
        results_df: per-sample results with scores, risk, evidence, persistence.
        events_list: grouped anomaly events.
    """
    from anomaly_detection.anomaly_scoring import (
        normalize_anomaly_scores,
        assign_risk_levels_batch,
    )
    from anomaly_detection.explainability import explain_anomaly
    from anomaly_detection.persistence import apply_persistence
    from anomaly_detection.event_grouping import group_anomaly_events

    # 1. Load artifacts
    artifacts = load_model_artifacts(model_dir)
    model = artifacts['model']
    scaler = artifacts['scaler']
    medians = artifacts['baseline_medians']
    mad = artifacts['baseline_mad']
    score_config = artifacts['score_config']
    score_min = score_config['score_min']
    score_max = score_config['score_max']

    feature_list = artifacts['feature_config']['model_features']

    # 2. Validate required columns
    missing_cols = [c for c in feature_list if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")

    # 3. Separate ground truth (NEVER used for inference)
    y_true = None
    if 'anomaly_label' in df.columns:
        y_true = df['anomaly_label'].values.copy()

    # 4. Extract communication gap context
    comm_gap = df['communication_gap_flag'].values.copy() if 'communication_gap_flag' in df.columns else np.zeros(len(df))

    # 5. Prepare feature matrix — ONLY model features
    X = df[feature_list].copy()

    # 6. Handle NaNs — fill with 0 for inference (NaN = no signal, not failure)
    nan_counts = X.isnull().sum(axis=1).values
    X = X.fillna(0)

    # 7. Scale using TRAINING-fitted scaler
    X_scaled = scaler.transform(X)

    # 8. Run Isolation Forest inference
    t_start = time.perf_counter()
    raw_scores = model.decision_function(X_scaled)
    t_end = time.perf_counter()
    inference_time_ms = (t_end - t_start) * 1000
    per_sample_ms = inference_time_ms / len(X_scaled)

    logger.info(f"Inference: {len(X_scaled)} samples in {inference_time_ms:.1f}ms ({per_sample_ms:.3f}ms/sample)")

    # 9. Normalize scores
    anomaly_scores = normalize_anomaly_scores(raw_scores, score_min, score_max)

    # 10. Risk levels
    risk_levels = assign_risk_levels_batch(anomaly_scores)

    # 11. Explainability for each sample
    explanations = []
    for i in range(len(df)):
        sample = X.iloc[i]
        expl = explain_anomaly(sample, medians, mad, top_n=5)
        explanations.append(expl)

    # 12. Communication-gap override
    data_quality_warnings = []
    for i in range(len(df)):
        if comm_gap[i] == 1 or nan_counts[i] > len(feature_list) * 0.3:
            data_quality_warnings.append(True)
            # Reduce confidence — do not claim mechanical failure during blackout
            risk_levels[i] = 'NORMAL'
            anomaly_scores[i] = 0.0
        else:
            data_quality_warnings.append(False)

    # 13. Temporal persistence
    persistence_states = apply_persistence(anomaly_scores)

    # 14. Build results DataFrame
    results = df[['timestamp']].copy()
    results['asset_id'] = asset_id
    results['data_type'] = 'SYNTHETIC_DATA'
    results['anomaly_score'] = anomaly_scores
    results['risk_level'] = risk_levels
    results['persistence_state'] = persistence_states
    results['evidence_pattern'] = [e['evidence_pattern'] for e in explanations]
    results['supporting_domains'] = [e['supporting_domains'] for e in explanations]
    results['contributing_signals'] = [
        [s['feature'] for s in e['contributing_signals'] if s['contribution'] in ('HIGH', 'MEDIUM')]
        for e in explanations
    ]
    results['data_quality_warning'] = data_quality_warnings
    results['anomaly_detected'] = (
        (results['persistence_state'] == 'PERSISTENT') & (~results['data_quality_warning'])
    )

    # Confidence based on evidence strength
    def _confidence(row):
        if row['data_quality_warning']:
            return 'LOW'
        if row['persistence_state'] == 'PERSISTENT' and row['evidence_pattern'] == 'CROSS_DOMAIN':
            return 'HIGH'
        if row['persistence_state'] == 'PERSISTENT':
            return 'MEDIUM'
        return 'LOW'
    results['confidence'] = results.apply(_confidence, axis=1)

    if y_true is not None:
        results['y_true'] = y_true

    results['inference_time_ms_per_sample'] = round(per_sample_ms, 4)

    # 15. Group events
    events = group_anomaly_events(results, asset_id=asset_id)

    return results, events

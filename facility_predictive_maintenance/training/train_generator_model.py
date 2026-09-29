"""
Training Pipeline — Generator Anomaly Detection Model
Project: POLAR-TWIN — Facility Predictive Maintenance
Asset: Diesel Generator

Trains an Isolation Forest on HEALTHY generator telemetry only.
The model learns the baseline of normal multivariate operating behavior.

Ground-truth labels (anomaly_label, anomaly_type) are NEVER used as features.
The scaler is fitted ONLY on the training split.
Chronological splitting is used — NO random shuffle.

All data is SYNTHETIC DATA for SIH 2026 demonstration.
"""
import pandas as pd
import numpy as np
import json
import joblib
import logging
import sys
from pathlib import Path
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---

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

GROUND_TRUTH_FIELDS = ['anomaly_label', 'anomaly_type']
DECISION_CONTEXT_FIELDS = ['communication_gap_flag']

# Isolation Forest parameters
# contamination=0.01: Our training data is entirely healthy generator telemetry.
# At most ~1% of training points may be natural noise outliers (e.g., load transients).
# A low contamination value gives the model a generous normal envelope, which is
# appropriate when the training set contains NO known anomalies.
# Using 'auto' (sklearn default offset of -0.5) was too aggressive and produced
# a ~50% false positive rate on healthy validation data.
IF_PARAMS = {
    'n_estimators': 200,
    'contamination': 0.01,
    'max_samples': 'auto',
    'random_state': 42,
    'n_jobs': -1,
}

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
# TEST_RATIO = 0.15 (remainder)


def main():
    # --- PATHS ---
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    data_path = project_root / 'data' / 'processed' / 'generator_normal_features.csv'
    model_dir = project_root / 'models' / 'generator_model'
    model_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. LOAD DATA ---
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # --- 2. VALIDATE: ground truth must not enter features ---
    for gt_col in GROUND_TRUTH_FIELDS:
        if gt_col in MODEL_FEATURES:
            raise ValueError(f"DATA LEAKAGE: {gt_col} found in MODEL_FEATURES!")
    for ctx_col in DECISION_CONTEXT_FIELDS:
        if ctx_col in MODEL_FEATURES:
            raise ValueError(f"LEAKAGE: {ctx_col} found in MODEL_FEATURES! It must bypass the ML model.")
    logger.info("Leakage check PASSED: ground truth and decision context excluded from features.")

    # --- 3. SELECT FEATURES ---
    missing_features = [f for f in MODEL_FEATURES if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing features in dataset: {missing_features}")

    X_all = df[MODEL_FEATURES].copy()

    # --- 4. HANDLE NaNs ---
    # First few rows may have NaN from rolling features (warm-up period).
    # Drop them from training. They are a tiny fraction.
    nan_rows_before = X_all.isnull().any(axis=1).sum()
    logger.info(f"Rows with NaN before handling: {nan_rows_before}")
    # For training, we drop NaN rows rather than filling, to avoid introducing bias
    valid_mask = ~X_all.isnull().any(axis=1)
    X_valid = X_all[valid_mask].reset_index(drop=True)
    logger.info(f"Rows after dropping NaN: {len(X_valid)}")

    # --- 5. CHRONOLOGICAL SPLIT ---
    n = len(X_valid)
    train_end = int(n * TRAIN_RATIO)
    val_end = int(n * (TRAIN_RATIO + VAL_RATIO))

    X_train = X_valid.iloc[:train_end]
    X_val = X_valid.iloc[train_end:val_end]
    X_test = X_valid.iloc[val_end:]

    logger.info(f"Chronological split: TRAIN={len(X_train)}, VAL={len(X_val)}, TEST={len(X_test)}")

    # --- 6. FIT SCALER ON TRAINING DATA ONLY ---
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    logger.info("StandardScaler fitted on TRAINING data only.")

    # --- 7. FIT ISOLATION FOREST ON TRAINING DATA ONLY ---
    logger.info(f"Training Isolation Forest with params: {IF_PARAMS}")
    model = IsolationForest(**IF_PARAMS)
    model.fit(X_train_scaled)
    logger.info("Isolation Forest training complete.")

    # --- 8. COMPUTE RAW SCORES ON TRAINING DATA FOR SCORE NORMALIZATION ---
    raw_scores_train = model.decision_function(X_train_scaled)
    # Use 1st/99th percentiles for robust normalization with wider range
    score_min = float(np.percentile(raw_scores_train, 1))
    score_max = float(np.percentile(raw_scores_train, 99))
    logger.info(f"Score normalizer fitted: min={score_min:.4f}, max={score_max:.4f}")

    # --- 9. COMPUTE BASELINE STATS FOR EXPLAINABILITY ---
    # Using TRAINING data only
    baseline_medians = X_train.median()
    baseline_mad = (X_train - baseline_medians).abs().median()
    baseline_mad = baseline_mad.replace(0, 1e-6)
    logger.info("Baseline medians and MAD computed from training data.")

    # --- 10. SAVE ARTIFACTS ---
    joblib.dump(model, model_dir / 'isolation_forest.joblib')
    joblib.dump(scaler, model_dir / 'scaler.joblib')
    joblib.dump(baseline_medians, model_dir / 'baseline_medians.joblib')
    joblib.dump(baseline_mad, model_dir / 'baseline_mad.joblib')

    # Score config
    score_config = {
        'score_min': score_min,
        'score_max': score_max,
        'normalization_method': 'percentile_inversion',
        'normalization_note': '0.0=normal, 1.0=highly anomalous. NOT a probability.',
        'training_percentiles': {'low': 2, 'high': 98},
    }
    with open(model_dir / 'score_config.json', 'w') as f:
        json.dump(score_config, f, indent=2)

    # Feature config
    feature_config = {
        'model_features': MODEL_FEATURES,
        'decision_context_fields': DECISION_CONTEXT_FIELDS,
        'ground_truth_fields': GROUND_TRUTH_FIELDS,
        'note': 'ground_truth_fields are NEVER used as model inputs.',
    }
    with open(model_dir / 'feature_config.json', 'w') as f:
        json.dump(feature_config, f, indent=2)

    # Model metadata
    import sklearn
    metadata = {
        'model_type': 'IsolationForest',
        'model_version': '1.0.0',
        'project': 'POLAR-TWIN',
        'asset': 'Diesel Generator',
        'data_type': 'SYNTHETIC_DATA',
        'training_timestamp': datetime.now().isoformat(),
        'training_data': 'generator_normal_features.csv',
        'training_rows': len(X_train),
        'validation_rows': len(X_val),
        'test_rows': len(X_test),
        'feature_count': len(MODEL_FEATURES),
        'features': MODEL_FEATURES,
        'parameters': IF_PARAMS,
        'random_seed': IF_PARAMS['random_state'],
        'chronological_split': True,
        'split_ratios': {'train': TRAIN_RATIO, 'val': VAL_RATIO, 'test': 1 - TRAIN_RATIO - VAL_RATIO},
        'python_version': sys.version,
        'sklearn_version': sklearn.__version__,
        'scaler': 'StandardScaler',
        'scaler_fitted_on': 'training_data_only',
        'contamination_strategy': 'auto — sklearn determines from training data noise, not from anomaly labels',
    }
    with open(model_dir / 'model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info(f"All artifacts saved to {model_dir}")

    # --- 11. QUICK VALIDATION ON TRAINING/VAL ---
    raw_val = model.decision_function(X_val_scaled)
    from anomaly_detection.anomaly_scoring import normalize_anomaly_scores
    val_scores = normalize_anomaly_scores(raw_val, score_min, score_max)
    logger.info(f"Validation scores — mean: {val_scores.mean():.4f}, max: {val_scores.max():.4f}, min: {val_scores.min():.4f}")

    print("\n" + "=" * 50)
    print("TRAINING COMPLETE")
    print("=" * 50)
    print(f"Model: IsolationForest (n_estimators={IF_PARAMS['n_estimators']})")
    print(f"Training rows: {len(X_train)}")
    print(f"Validation rows: {len(X_val)}")
    print(f"Test rows: {len(X_test)}")
    print(f"Features: {len(MODEL_FEATURES)}")
    print(f"Artifacts: {model_dir}")
    print(f"Val score mean: {val_scores.mean():.4f}")
    print(f"Val score max: {val_scores.max():.4f}")
    print("=" * 50)


if __name__ == '__main__':
    main()

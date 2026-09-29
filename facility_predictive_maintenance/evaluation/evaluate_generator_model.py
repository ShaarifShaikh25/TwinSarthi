"""
Evaluation Pipeline — Generator Anomaly Detection
Project: POLAR-TWIN — Facility Predictive Maintenance
Asset: Diesel Generator

Evaluates the trained Isolation Forest model against:
  - Case A: Normal operation (false positive assessment)
  - Case B: Combustion degradation (detection capability + delay)
  - Case C: Communication gap (must NOT trigger mechanical failure)
  - Case D: Sensor fault (should be single-signal, not combustion failure)

Ground truth is used ONLY after inference for metric calculation.
All data is SYNTHETIC DATA.
"""
import pandas as pd
import numpy as np
import json
import logging
import sys
import os
import time
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from anomaly_detection.generator_anomaly import run_generator_anomaly_detection


def evaluate_scenario(
    df: pd.DataFrame,
    model_dir: Path,
    scenario_name: str,
    asset_id: str = 'DG-01',
) -> dict:
    """
    Run inference and evaluate against ground truth for a single scenario.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"EVALUATING: {scenario_name}")
    logger.info(f"{'='*60}")

    # Run full pipeline
    results_df, events = run_generator_anomaly_detection(df, model_dir, asset_id)

    report = {
        'scenario': scenario_name,
        'data_type': 'SYNTHETIC_DATA',
        'total_samples': len(results_df),
    }

    # --- Metrics against ground truth (if available) ---
    if 'y_true' in results_df.columns:
        y_true = results_df['y_true'].values.astype(int)
        y_pred = results_df['anomaly_detected'].astype(int).values

        # Guard against single-class scenarios
        unique_true = np.unique(y_true)
        unique_pred = np.unique(y_pred)

        if len(unique_true) > 1 or len(unique_pred) > 1:
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

            report['precision'] = round(float(precision), 4)
            report['recall'] = round(float(recall), 4)
            report['f1_score'] = round(float(f1), 4)
            report['false_positive_rate'] = round(float(fpr), 4)
            report['false_negative_rate'] = round(float(fnr), 4)
            report['true_positives'] = int(tp)
            report['false_positives'] = int(fp)
            report['true_negatives'] = int(tn)
            report['false_negatives'] = int(fn)
        else:
            # Single-class scenario (e.g., all normal or all communication gap)
            if y_true.sum() == 0:
                # All normal — measure false positives
                fp = y_pred.sum()
                report['false_positives'] = int(fp)
                report['false_positive_rate'] = round(float(fp / len(y_pred)), 4) if len(y_pred) > 0 else 0.0
                report['note'] = 'Single-class (all NORMAL). Precision/Recall/F1 not applicable.'
            else:
                report['note'] = 'Single-class scenario. Standard metrics not applicable.'

        # --- Detection Delay ---
        # For scenarios with anomaly onset, calculate how long after ground truth onset
        # the model first detects a PERSISTENT anomaly.
        if y_true.sum() > 0:
            gt_onset_idx = np.argmax(y_true == 1)
            persistent_mask = (results_df['persistence_state'] == 'PERSISTENT').values
            if persistent_mask.any():
                first_detection_idx = np.argmax(persistent_mask)
                if first_detection_idx >= gt_onset_idx:
                    delay_samples = first_detection_idx - gt_onset_idx
                    report['detection_delay_samples'] = int(delay_samples)
                    report['detection_delay_minutes'] = int(delay_samples)  # 1-min sampling
                else:
                    report['detection_delay_minutes'] = 0
                    report['note_detection'] = 'Model detected before ground truth onset (possible noise).'
            else:
                report['detection_delay_minutes'] = 'NOT_DETECTED'

    # --- Data Quality Warnings ---
    dq_warnings = results_df['data_quality_warning'].sum()
    report['data_quality_warnings'] = int(dq_warnings)

    # --- Persistence distribution ---
    persistence_counts = results_df['persistence_state'].value_counts().to_dict()
    report['persistence_distribution'] = persistence_counts

    # --- Events ---
    report['events_detected'] = len(events)
    if events:
        report['events'] = events

    # --- Score statistics ---
    scores = results_df['anomaly_score'].values
    report['score_mean'] = round(float(np.mean(scores)), 4)
    report['score_max'] = round(float(np.max(scores)), 4)
    report['score_std'] = round(float(np.std(scores)), 4)

    # --- Inference performance ---
    if 'inference_time_ms_per_sample' in results_df.columns:
        report['inference_time_ms_per_sample'] = round(float(results_df['inference_time_ms_per_sample'].iloc[0]), 4)

    # --- Evidence patterns ---
    evidence_counts = results_df['evidence_pattern'].value_counts().to_dict()
    report['evidence_patterns'] = evidence_counts

    return report


def main():
    model_dir = project_root / 'models' / 'generator_model'
    processed_dir = project_root / 'data' / 'processed'
    eval_output_dir = project_root / 'evaluation'
    eval_output_dir.mkdir(parents=True, exist_ok=True)

    # Check model exists
    if not (model_dir / 'isolation_forest.joblib').exists():
        logger.error("Model not found! Run train_generator_model.py first.")
        sys.exit(1)

    # --- Scenarios ---
    scenarios = {
        'Case_A_Normal': 'generator_normal_features.csv',
        'Case_B_Combustion_Degradation': 'generator_combustion_degradation_features.csv',
        'Case_C_Communication_Gap': 'generator_communication_gap_features.csv',
        'Case_D_Sensor_Fault': 'generator_sensor_fault_features.csv',
    }

    all_reports = []

    for scenario_name, filename in scenarios.items():
        filepath = processed_dir / filename
        if not filepath.exists():
            logger.warning(f"Skipping {scenario_name}: {filepath} not found.")
            continue

        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        report = evaluate_scenario(df, model_dir, scenario_name)
        all_reports.append(report)

        # Print summary
        print(f"\n--- {scenario_name} ---")
        for k, v in report.items():
            if k != 'events':  # Don't print full events inline
                print(f"  {k}: {v}")

    # --- Model artifacts info ---
    model_size = os.path.getsize(model_dir / 'isolation_forest.joblib') / 1024
    scaler_size = os.path.getsize(model_dir / 'scaler.joblib') / 1024

    summary = {
        'project': 'POLAR-TWIN',
        'phase': 'Phase 4 — Multivariate Generator Anomaly Detection',
        'data_type': 'SYNTHETIC_DATA',
        'model': 'IsolationForest',
        'model_size_kb': round(model_size, 1),
        'scaler_size_kb': round(scaler_size, 1),
        'scenarios': all_reports,
    }

    # Save full report
    report_path = eval_output_dir / 'generator_evaluation_report.json'
    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"Full evaluation report saved to: {report_path}")
    print(f"Model size: {model_size:.1f} KB")
    print(f"Scaler size: {scaler_size:.1f} KB")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()

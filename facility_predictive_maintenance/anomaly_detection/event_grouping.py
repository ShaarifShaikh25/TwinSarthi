"""
Event Grouping Module
Project: POLAR-TWIN — Facility Predictive Maintenance
Asset: Diesel Generator

Groups consecutive PERSISTENT anomaly points into discrete anomaly events
rather than producing thousands of per-minute alerts.

Each event contains:
  - event_id, asset_id
  - start_time, end_time, duration_minutes
  - peak/mean anomaly score
  - risk level
  - evidence pattern and supporting domains
  - data quality status
"""
from collections import Counter
from typing import List, Dict, Optional
import pandas as pd
import numpy as np


def group_anomaly_events(
    df: pd.DataFrame,
    timestamp_col: str = 'timestamp',
    score_col: str = 'anomaly_score',
    persistence_col: str = 'persistence_state',
    risk_col: str = 'risk_level',
    evidence_pattern_col: str = 'evidence_pattern',
    supporting_domains_col: str = 'supporting_domains',
    data_quality_col: str = 'data_quality_warning',
    asset_id: str = 'DG-01',
) -> List[Dict]:
    """
    Scan the results dataframe and group consecutive PERSISTENT rows
    into discrete anomaly events.

    Returns a list of event dictionaries.
    """
    events: List[Dict] = []
    in_event = False
    event_start = None
    event_scores: List[float] = []
    event_risks: List[str] = []
    event_patterns: List[str] = []
    event_domains: List = []
    event_dq: List[bool] = []
    event_counter = 0

    for idx, row in df.iterrows():
        state = row.get(persistence_col, 'NORMAL')

        if state == 'PERSISTENT':
            if not in_event:
                # Start new event
                in_event = True
                event_start = row[timestamp_col]
                event_scores = []
                event_risks = []
                event_patterns = []
                event_domains = []
                event_dq = []

            event_scores.append(row[score_col])
            event_risks.append(row.get(risk_col, 'UNKNOWN'))
            event_patterns.append(row.get(evidence_pattern_col, 'UNKNOWN'))
            if supporting_domains_col in row and isinstance(row[supporting_domains_col], list):
                event_domains.extend(row[supporting_domains_col])
            event_dq.append(row.get(data_quality_col, False))
        else:
            if in_event:
                # Close the event
                event_counter += 1
                event_end = df.loc[idx - 1 if idx > 0 else idx, timestamp_col]
                duration = (pd.Timestamp(event_end) - pd.Timestamp(event_start)).total_seconds() / 60.0

                # Most severe risk in the event
                risk_order = {'NORMAL': 0, 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
                peak_risk = max(event_risks, key=lambda r: risk_order.get(r, 0))

                # Most common evidence pattern
                if event_patterns:
                    pattern_counts = Counter(event_patterns)
                    dominant_pattern = pattern_counts.most_common(1)[0][0]
                else:
                    dominant_pattern = 'UNKNOWN'

                events.append({
                    'event_id': f'EVT-{asset_id}-{event_counter:04d}',
                    'asset_id': asset_id,
                    'data_type': 'SYNTHETIC_DATA',
                    'start_time': str(event_start),
                    'end_time': str(event_end),
                    'duration_minutes': round(duration, 1),
                    'peak_anomaly_score': round(float(np.max(event_scores)), 4),
                    'mean_anomaly_score': round(float(np.mean(event_scores)), 4),
                    'risk_level': peak_risk,
                    'evidence_pattern': dominant_pattern,
                    'supporting_domains': sorted(list(set(event_domains))),
                    'data_quality_warning': any(event_dq),
                    'num_samples': len(event_scores),
                })
                in_event = False

    # Close any event still open at end of data
    if in_event and event_scores:
        event_counter += 1
        event_end = df.iloc[-1][timestamp_col]
        duration = (pd.Timestamp(event_end) - pd.Timestamp(event_start)).total_seconds() / 60.0
        risk_order = {'NORMAL': 0, 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        peak_risk = max(event_risks, key=lambda r: risk_order.get(r, 0))
        pattern_counts = Counter(event_patterns)
        dominant_pattern = pattern_counts.most_common(1)[0][0] if event_patterns else 'UNKNOWN'

        events.append({
            'event_id': f'EVT-{asset_id}-{event_counter:04d}',
            'asset_id': asset_id,
            'data_type': 'SYNTHETIC_DATA',
            'start_time': str(event_start),
            'end_time': str(event_end),
            'duration_minutes': round(duration, 1),
            'peak_anomaly_score': round(float(np.max(event_scores)), 4),
            'mean_anomaly_score': round(float(np.mean(event_scores)), 4),
            'risk_level': peak_risk,
            'evidence_pattern': dominant_pattern,
            'supporting_domains': sorted(list(set(event_domains))),
            'data_quality_warning': any(event_dq),
            'num_samples': len(event_scores),
        })

    return events

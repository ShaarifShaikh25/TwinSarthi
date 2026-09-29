import pandas as pd

def assess_data_quality(df: pd.DataFrame, dataset_name: str, time_col: str = 'timestamp') -> dict:
    total_rows = len(df)
    duplicate_rows = df.duplicated().sum()
    duplicate_timestamps = df.duplicated(subset=[time_col]).sum() if time_col in df.columns else 0
    missing_values = df.isnull().sum().to_dict()
    missing_pct = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
    
    gaps = 0
    max_gap = 0
    if time_col in df.columns and total_rows > 1:
        df_sorted = df.sort_values(time_col)
        time_diffs = df_sorted[time_col].diff().dt.total_seconds() / 60.0
        # Assume > 5 mins is a communication gap
        gaps = (time_diffs > 5).sum()
        max_gap = time_diffs.max() if gaps > 0 else 0
        
    status = "DEGRADED" if (missing_pct > 5 or gaps > 0 or duplicate_rows > 0) else "HEALTHY"
    
    report = {
        "dataset": dataset_name,
        "total_rows": int(total_rows),
        "duplicate_rows": int(duplicate_rows),
        "duplicate_timestamps": int(duplicate_timestamps),
        "missing_values": {k: int(v) for k, v in missing_values.items() if v > 0},
        "missing_percentage": float(round(missing_pct, 2)),
        "communication_gaps": int(gaps),
        "largest_gap_minutes": float(round(max_gap, 2)) if pd.notnull(max_gap) else 0.0,
        "quality_status": status
    }
    return report

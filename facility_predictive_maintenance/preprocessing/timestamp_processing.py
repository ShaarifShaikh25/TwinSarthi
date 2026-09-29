import pandas as pd

def normalize_timestamps(df: pd.DataFrame, time_col: str = 'timestamp', expected_freq: str = '1min') -> pd.DataFrame:
    """
    Sorts, removes duplicate timestamps, and identifies communication gaps.
    Missing intervals are reindexed, but values are left as NaN.
    Adds communication_gap_flag.
    """
    df_out = df.copy()
    df_out[time_col] = pd.to_datetime(df_out[time_col])
    
    # Sort and drop duplicate timestamps (keep first)
    df_out = df_out.sort_values(time_col).drop_duplicates(subset=[time_col], keep='first')
    
    # Reindex to enforce strict frequency
    df_out = df_out.set_index(time_col)
    full_index = pd.date_range(start=df_out.index.min(), end=df_out.index.max(), freq=expected_freq)
    df_out = df_out.reindex(full_index)
    df_out.index.name = time_col
    df_out = df_out.reset_index()
    
    # Create communication gap flag: 1 if the timestamp was missing in original data
    # If 'rpm' (or another primary sensor) is NaN after reindexing, it was a gap.
    df_out['communication_gap_flag'] = df_out['rpm'].isnull().astype(int)
    
    return df_out

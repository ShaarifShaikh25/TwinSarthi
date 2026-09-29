import pandas as pd

def handle_missing_data(df: pd.DataFrame, cols_to_interpolate: list, max_interp_limit: int = 3) -> pd.DataFrame:
    """
    Intelligently handles missing data. 
    Short gaps (<= max_interp_limit) are interpolated.
    Long gaps are left as NaN, explicitly representing communication blackouts.
    """
    df_out = df.copy()
    df_out[cols_to_interpolate] = df_out[cols_to_interpolate].interpolate(method='linear', limit=max_interp_limit)
    return df_out

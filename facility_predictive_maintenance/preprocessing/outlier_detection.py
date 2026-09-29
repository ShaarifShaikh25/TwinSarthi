import pandas as pd
import numpy as np

def flag_statistical_outliers(df: pd.DataFrame, columns: list, std_devs: float = 3.0) -> pd.DataFrame:
    """
    Flags statistical outliers using rolling z-score.
    Does not delete them, as anomalies are often statistical outliers.
    0=NORMAL, 1=SUSPICIOUS, 2=POSSIBLE_ANOMALY
    """
    df_out = df.copy()
    for col in columns:
        rolling_mean = df_out[col].rolling(window=60, min_periods=1).mean()
        rolling_std = df_out[col].rolling(window=60, min_periods=1).std().replace(0, np.nan)
        z_score = (df_out[col] - rolling_mean) / rolling_std
        
        flag_col = f"{col}_outlier_flag"
        df_out[flag_col] = 0 
        df_out.loc[z_score.abs() > std_devs, flag_col] = 1 
        df_out.loc[z_score.abs() > (std_devs * 1.5), flag_col] = 2 
        
    return df_out

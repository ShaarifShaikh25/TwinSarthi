"""
Weather Simulator
Generates synthetic, physically plausible weather telemetry for Antarctic stations.

IMPORTANT: All data is SIMULATION / DEMO DATA.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any

class WeatherSimulator:
    """
    Generates a continuous time series using a random walk with mean reversion
    to avoid impossible spikes while simulating natural drift.
    """
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def generate_series(
        self,
        start_time: str,
        periods: int,
        interval_minutes: int,
        base_temp: float = -15.0,
        temp_volatility: float = 0.5,
        base_wind: float = 10.0,
        wind_volatility: float = 1.0,
        base_humidity: float = 60.0,
        humidity_volatility: float = 2.0
    ) -> pd.DataFrame:
        """
        Generate weather parameters over a specified time window.
        """
        timestamps = pd.date_range(start=start_time, periods=periods, freq=f'{interval_minutes}min')
        
        def generate_walk(base: float, vol: float, min_val: float, max_val: float, reversion_strength: float = 0.1):
            values = [base]
            for _ in range(1, periods):
                drift = (base - values[-1]) * reversion_strength
                step = self.rng.normal(loc=drift, scale=vol)
                new_val = float(np.clip(values[-1] + step, min_val, max_val))
                values.append(new_val)
            return values

        temperatures = generate_walk(base_temp, temp_volatility, -89.2, 10.0)
        winds = generate_walk(base_wind, wind_volatility, 0.0, 60.0)
        humidities = generate_walk(base_humidity, humidity_volatility, 0.0, 100.0)
        
        conditions = []
        for t, w in zip(temperatures, winds):
            if w > 20:
                conditions.append("WINDY")
            elif t < -30:
                conditions.append("COLD")
            else:
                conditions.append("NORMAL")
                
        df = pd.DataFrame({
            'timestamp': timestamps,
            'temperature_c': np.round(temperatures, 2),
            'wind_speed_mps': np.round(winds, 2),
            'humidity_percent': np.round(humidities, 2),
            'weather_condition': conditions
        })
        
        return df

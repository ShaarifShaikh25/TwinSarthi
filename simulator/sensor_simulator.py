"""
Sensor Simulator
Generates station telemetry incorporating weather and basic station identity.

IMPORTANT: All data is SIMULATION / DEMO DATA.
"""
from typing import List, Dict, Any, Optional
from simulator.weather_simulator import WeatherSimulator

def generate_sensor_series(
    station_id: str,
    start_time: str,
    periods: int,
    interval_minutes: int,
    seed: Optional[int] = 42,
    weather_kwargs: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Generates synthetic sensor telemetry for a given station.
    """
    if weather_kwargs is None:
        weather_kwargs = {}
        
    ws = WeatherSimulator(seed=seed if seed is not None else 42)
    weather_df = ws.generate_series(
        start_time=start_time,
        periods=periods,
        interval_minutes=interval_minutes,
        **weather_kwargs
    )
    
    # Format to required structure
    records = []
    for _, row in weather_df.iterrows():
        record = {
            "timestamp": row['timestamp'].isoformat(),
            "station_id": station_id,
            "temperature_c": float(row['temperature_c']),
            "wind_speed_mps": float(row['wind_speed_mps']),
            "humidity_percent": float(row['humidity_percent']),
            "weather_condition": str(row['weather_condition'])
        }
        records.append(record)
        
    return records
    
if __name__ == "__main__":
    import json
    print("Generating sample telemetry for MAITRI...")
    sample = generate_sensor_series("MAITRI", "2026-01-01T00:00:00", 5, 60)
    print(json.dumps(sample, indent=2))

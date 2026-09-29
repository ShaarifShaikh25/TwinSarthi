"""
Normal Scenario Generator
IMPORTANT: All data is SIMULATION / DEMO DATA.
"""
from typing import List, Dict, Any
from simulator.sensor_simulator import generate_sensor_series
from simulator.energy_simulator import EnergySimulator
from simulator.fuel_simulator import FuelSimulator
from simulator.logistics_simulator import LogisticsSimulator

def generate_normal_scenario(
    station_id: str = "MAITRI",
    start_time: str = "2026-01-01T00:00:00",
    periods: int = 24,
    interval_minutes: int = 60,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generates a normal station telemetry sequence encompassing environment,
    energy, generator state, fuel, and logistics.
    """
    # 1. Environment Simulation
    if station_id == "MAITRI":
        base_temp = -10.0
        base_wind = 8.0
    else:  
        base_temp = -8.0
        base_wind = 12.0
        
    weather_kwargs = {
        'base_temp': base_temp,
        'base_wind': base_wind,
        'temp_volatility': 0.3,
        'wind_volatility': 0.8
    }
    
    # We use Step 1 generator for base weather data
    environmental_records = generate_sensor_series(
        station_id=station_id,
        start_time=start_time,
        periods=periods,
        interval_minutes=interval_minutes,
        seed=seed,
        weather_kwargs=weather_kwargs
    )
    
    # 2. Initialize State Simulators
    energy_sim = EnergySimulator()
    fuel_sim = FuelSimulator()
    logistics_sim = LogisticsSimulator()
    
    generator_status = "RUNNING"
    generator_runtime_hours = 1000.0 # Initial mock runtime
    
    complete_telemetry = []
    
    # 3. Sequential Cascade Simulation
    for record in environmental_records:
        temp = record["temperature_c"]
        wind = record["wind_speed_mps"]
        
        # Energy
        energy_state = energy_sim.calculate_energy_state(temperature_c=temp, wind_speed_mps=wind)
        
        # Generator
        gen_load = energy_state["generator_load_percent"]
        generator_runtime_hours += (interval_minutes / 60.0)
        
        generator_state = {
            "status": generator_status,
            "runtime_hours": round(generator_runtime_hours, 2)
        }
        
        # Fuel
        fuel_state = fuel_sim.calculate_fuel_state(generator_load_percent=gen_load, interval_minutes=interval_minutes)
        
        # Logistics
        logistics_state = logistics_sim.calculate_logistics_state(interval_minutes=interval_minutes)
        
        # Construct Nested Output
        telemetry_frame = {
            "timestamp": record["timestamp"],
            "station_id": record["station_id"],
            "environment": {
                "temperature_c": record["temperature_c"],
                "wind_speed_mps": record["wind_speed_mps"],
                "humidity_percent": record["humidity_percent"],
                "weather_condition": record["weather_condition"]
            },
            "energy": energy_state,
            "generator": generator_state,
            "fuel": fuel_state,
            "inventory": logistics_state
        }
        
        complete_telemetry.append(telemetry_frame)
        
    return complete_telemetry

if __name__ == '__main__':
    import json
    print('Generating sequential simulated telemetry record for MAITRI...')
    sample = generate_normal_scenario(periods=2, interval_minutes=60)
    print(json.dumps(sample, indent=2))


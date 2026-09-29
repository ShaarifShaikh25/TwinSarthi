"""
Fuel Simulator
Simulates fuel consumption and tank levels driven by generator load.

IMPORTANT: All data is SIMULATION / DEMO DATA.
PROTOTYPE SIMULATION PARAMETERS
"""
from typing import Dict, Any

class FuelSimulator:
    def __init__(self, initial_level_liters: float = 10000.0, base_lph: float = 10.0, load_factor: float = 0.4):
        self.level_liters = max(0.0, initial_level_liters)
        self.base_lph = base_lph
        self.load_factor = load_factor
        
    def calculate_fuel_state(self, generator_load_percent: float, interval_minutes: float) -> Dict[str, Any]:
        """
        Calculates fuel consumption based on generator load, updates fuel level, 
        and estimates remaining days.
        """
        # Consumption linearly related to load
        consumption_lph = self.base_lph + (generator_load_percent * self.load_factor)
        consumption_lpd = consumption_lph * 24.0
        
        # Reduce tank level
        interval_hours = interval_minutes / 60.0
        fuel_burned = consumption_lph * interval_hours
        
        self.level_liters = max(0.0, self.level_liters - fuel_burned)
        
        # Estimate days remaining
        days_remaining = self.level_liters / consumption_lpd if consumption_lpd > 0 else 0.0
        
        return {
            "level_liters": round(float(self.level_liters), 2),
            "consumption_lph": round(float(consumption_lph), 2),
            "consumption_lpd": round(float(consumption_lpd), 2),
            "days_remaining": round(float(days_remaining), 2)
        }

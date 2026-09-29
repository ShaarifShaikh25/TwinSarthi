"""
Energy Simulator
Simulates power consumption, HVAC load, and generator load driven by environmental factors.

IMPORTANT: All data is SIMULATION / DEMO DATA.
PROTOTYPE SIMULATION PARAMETERS
"""
from typing import Dict, Any
import numpy as np

class EnergySimulator:
    def __init__(self, generator_capacity_kw: float = 250.0, base_load_kw: float = 100.0, base_hvac_kw: float = 40.0):
        self.generator_capacity_kw = generator_capacity_kw
        self.base_load_kw = base_load_kw
        self.base_hvac_kw = base_hvac_kw
        
    def calculate_energy_state(self, temperature_c: float, wind_speed_mps: float) -> Dict[str, Any]:
        """
        Calculate energy demand driven by environmental factors.
        Lower temperature increases HVAC demand. Higher wind slightly increases HVAC demand due to heat loss.
        """
        # HVAC increases by 2 kW for every degree below -5C
        temp_delta = max(0.0, -5.0 - temperature_c)
        hvac_temp_load = temp_delta * 2.0
        
        # Wind increases HVAC load slightly (0.5 kW per mps over 5 mps)
        wind_delta = max(0.0, wind_speed_mps - 5.0)
        hvac_wind_load = wind_delta * 0.5
        
        hvac_load_kw = self.base_hvac_kw + hvac_temp_load + hvac_wind_load
        
        # Total power consumption
        power_consumption_kw = self.base_load_kw + hvac_load_kw
        
        # Generator load
        generator_load_percent = (power_consumption_kw / self.generator_capacity_kw) * 100.0
        
        return {
            "power_consumption_kw": round(float(power_consumption_kw), 2),
            "hvac_load_kw": round(float(hvac_load_kw), 2),
            "generator_load_percent": round(float(np.clip(generator_load_percent, 0.0, 100.0)), 2)
        }

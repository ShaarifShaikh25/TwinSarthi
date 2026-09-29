"""digital_twin/energy_twin.py

Defines the deterministic *Energy Twin* – a snapshot of a station's energy
related metrics derived from the latest telemetry values.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class EnergyTwin(BaseModel):
    generator_load: Optional[float] = Field(None, description="Load % of generator")
    fuel_level: Optional[float] = Field(None, description="Fuel level in liters")
    power_consumption: Optional[float] = Field(None, description="Power consumption in kW")
    power_generation: Optional[float] = Field(None, description="Power generated in kW")
    fuel_percentage: Optional[float] = None
    estimated_fuel_remaining_hours: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True

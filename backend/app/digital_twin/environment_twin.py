"""digital_twin/environment_twin.py

Defines the deterministic *Environment Twin* – a snapshot of the station's
environmental conditions derived from the latest telemetry of relevant sensors.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class EnvironmentTwin(BaseModel):
    temperature: Optional[float] = Field(None, description="Temperature in °C")
    wind: Optional[float] = Field(None, description="Wind speed in m/s")
    pressure: Optional[float] = Field(None, description="Atmospheric pressure hPa")
    humidity: Optional[float] = Field(None, description="Relative humidity %")
    visibility: Optional[float] = Field(None, description="Visibility in km")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True

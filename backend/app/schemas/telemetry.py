from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TelemetryBase(BaseModel):
    station_code: str
    sensor_id: int
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp")
    value: float
    quality: str = "GOOD"
    source: Optional[str] = "SIMULATED"


class TelemetryOut(BaseModel):
    id: int
    sensor_id: int
    timestamp: datetime
    value: float
    quality: str
    source: str

    class Config:
        orm_mode = True

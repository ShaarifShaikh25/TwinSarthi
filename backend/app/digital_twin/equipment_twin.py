"""digital_twin/equipment_twin.py

Defines the deterministic *Equipment Twin* – a snapshot of each piece of
equipment at a station, derived from the latest telemetry and maintenance
records.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class EquipmentTwin(BaseModel):
    equipment_id: int = Field(..., description="Database identifier of the equipment")
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    health_score: Optional[float] = Field(None, description="Score 0‑100")
    last_telemetry: Optional[Dict[str, Any]] = Field(default_factory=dict)
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True

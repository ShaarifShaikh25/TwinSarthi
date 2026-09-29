"""digital_twin/station_twin.py

This module defines the data structures representing the *Station Twin* – the
current digital state of a station. The representation is deliberately simple
and independent of any persistence layer; it is used by the twin service to
assemble the unified view returned by the API.

We use Pydantic models because they provide validation, JSON serialization and
are lightweight. The twins are *deterministic* – any derived fields are
computed in plain Python without ML.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class AlertInfo(BaseModel):
    id: int
    type: str
    severity: str
    message: str
    status: str
    created_at: datetime


class StationTwin(BaseModel):
    """Unified station digital twin.

    Contains high‑level identity / status fields and references to the
    sub‑twins (environment, energy, equipment, logistics). ``alerts`` holds a
    list of active alerts for the station.
    """

    station_id: int = Field(..., description="Database identifier of the station")
    name: Optional[str] = None
    code: Optional[str] = None
    status: Optional[str] = None
    environment: Dict[str, Any] = Field(default_factory=dict)
    energy: Dict[str, Any] = Field(default_factory=dict)
    equipment: Dict[str, Any] = Field(default_factory=dict)
    logistics: Dict[str, Any] = Field(default_factory=dict)
    alerts: List[AlertInfo] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    data_source: Optional[str] = None

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

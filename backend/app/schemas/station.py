"""app/schemas/station.py

Pydantic schemas for Stations, Equipment, Sensors, and Inventory.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class StationBase(BaseModel):
    name: str
    code: str
    latitude: float
    longitude: float
    status: str = "active"


class StationCreate(StationBase):
    pass


class StationOut(StationBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EquipmentCreate(BaseModel):
    station_id: int
    name: str
    type: str
    status: str = "operational"
    health_score: Optional[float] = 100.0


class EquipmentOut(BaseModel):
    id: int
    station_id: int
    name: str
    type: str
    status: str
    health_score: Optional[float] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None

    class Config:
        from_attributes = True


class SensorCreate(BaseModel):
    station_id: int
    equipment_id: Optional[int] = None
    type: str
    unit: str
    status: str = "active"


class SensorOut(BaseModel):
    id: int
    station_id: int
    equipment_id: Optional[int] = None
    type: str
    unit: str
    status: str

    class Config:
        from_attributes = True


class InventoryCreate(BaseModel):
    station_id: int
    item_name: str
    category: str
    quantity: float
    unit: str
    consumption_rate: Optional[float] = None
    minimum_required: Optional[float] = None


class InventoryOut(BaseModel):
    id: int
    station_id: int
    item_name: str
    category: str
    quantity: float
    unit: str
    consumption_rate: Optional[float] = None
    minimum_required: Optional[float] = None

    class Config:
        from_attributes = True

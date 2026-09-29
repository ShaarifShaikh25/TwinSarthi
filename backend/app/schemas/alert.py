from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AlertOut(BaseModel):
    id: int
    station_id: int
    severity: str
    type: str
    message: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertUpdateResponse(BaseModel):
    id: int
    station_id: int
    status: str
    message: str
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

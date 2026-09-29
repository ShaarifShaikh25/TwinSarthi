"""digital_twin/logistics_twin.py

Defines the deterministic *Logistics Twin* – a snapshot of inventory and
consumption metrics for a station. All values are derived from the latest
inventory records and telemetry (e.g., fuel consumption).
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class LogisticsTwin(BaseModel):
    inventory: Dict[str, Any] = Field(default_factory=dict)
    consumption_rate: Optional[float] = Field(None, description="Units per day")
    minimum_required: Optional[float] = None
    estimated_days_remaining: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True

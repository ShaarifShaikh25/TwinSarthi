"""app/schemas/simulation.py

Pydantic schemas for the POLAR-TWIN simulation execution interface.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class SimulationRequest(BaseModel):
    station_id: str = Field(..., description="Station ID or station code (e.g. MAITRI, BHARATI)")
    scenario_type: str = Field(..., description="Scenario type, e.g. blizzard_survival, generator_outage, fuel_rationing")
    duration_hours: int = Field(default=24, ge=1, le=720, description="Simulation forecast horizon in hours")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Scenario-specific parameters")


class SimulationResult(BaseModel):
    simulation_id: str
    station_id: str
    scenario_type: str
    status: str
    duration_hours: int
    summary: str
    metrics: Dict[str, Any]
    generated_recommendations: List[Dict[str, Any]]
    executed_by: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

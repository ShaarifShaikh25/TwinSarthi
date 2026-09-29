"""app/schemas/recommendation.py

Pydantic schemas for AI/Risk recommendations and human-in-the-loop decisions.
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field


class RecommendationCreate(BaseModel):
    station_id: int
    type: str = "energy_conservation"
    severity: str = "medium"
    title: str
    reason: str
    recommended_action: str
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)


class RecommendationApproveRequest(BaseModel):
    notes: Optional[str] = Field(default=None, description="Optional operational approval notes")


class RecommendationModifyRequest(BaseModel):
    modified_action: str = Field(..., description="Controller revised action or instructions")
    notes: Optional[str] = Field(default=None, description="Rationale for modification")


class RecommendationRejectRequest(BaseModel):
    reason: str = Field(..., description="Operational reason for rejecting the recommendation")


class RecommendationAuditOut(BaseModel):
    id: int
    recommendation_id: int
    user_id: Optional[int] = None
    action: str
    previous_status: Optional[str] = None
    new_status: str
    notes: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationOut(BaseModel):
    id: int
    station_id: int
    type: str
    severity: str
    title: str
    reason: str
    recommended_action: str
    confidence: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[int] = None
    modified_action: Optional[str] = None
    decision_notes: Optional[str] = None
    audits: Optional[List[RecommendationAuditOut]] = None

    model_config = ConfigDict(from_attributes=True)

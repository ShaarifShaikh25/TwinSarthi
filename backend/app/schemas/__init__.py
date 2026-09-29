from typing import Optional, Any
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[Any] = None


from .auth import LoginRequest, TokenResponse, UserOut
from .recommendation import (
    RecommendationCreate,
    RecommendationOut,
    RecommendationApproveRequest,
    RecommendationModifyRequest,
    RecommendationRejectRequest,
)
from .simulation import SimulationRequest, SimulationResult

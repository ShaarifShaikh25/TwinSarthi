"""app/api/routes/recommendations.py

Recommendation Decision API Endpoints:
- POST /api/recommendations: Ingest AI/Risk recommendation
- GET /api/recommendations/{station_id}: List recommendations for a station
- POST /api/recommendations/{id}/approve: Approve recommendation (CONTROLLER / ADMIN)
- POST /api/recommendations/{id}/modify: Modify recommendation action (CONTROLLER / ADMIN)
- POST /api/recommendations/{id}/reject: Reject recommendation (CONTROLLER / ADMIN)
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.models.station import Station
from app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationOut,
    RecommendationApproveRequest,
    RecommendationModifyRequest,
    RecommendationRejectRequest,
)
from app.schemas import SuccessResponse
from app.services.recommendation_service import (
    create_recommendation,
    get_station_recommendations,
    get_recommendation_by_id,
    approve_recommendation,
    modify_recommendation,
    reject_recommendation,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recommendations"])


def _resolve_station(station_id: str, db: Session) -> Station:
    """Resolve station by integer ID or uppercase/lowercase station code."""
    norm = station_id.strip()
    if norm.isdigit():
        station = db.query(Station).filter(Station.id == int(norm)).first()
        if station:
            return station
    station = db.query(Station).filter(Station.code.ilike(norm)).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station '{station_id}' not found",
        )
    return station


def _serialize_rec(rec) -> dict:
    """Serialize recommendation entity to dictionary matching user format."""
    return {
        "id": rec.id,
        "station_id": rec.station_id,
        "type": rec.type,
        "severity": rec.severity.value if hasattr(rec.severity, "value") else str(rec.severity),
        "title": rec.title,
        "reason": rec.reason,
        "recommended_action": rec.recommended_action,
        "confidence": rec.confidence,
        "status": rec.status.value if hasattr(rec.status, "value") else str(rec.status),
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
        "decided_at": rec.decided_at.isoformat() if rec.decided_at else None,
        "decided_by": rec.decided_by,
        "modified_action": rec.modified_action,
        "decision_notes": rec.decision_notes,
    }


@router.post("", response_model=SuccessResponse)
def create_recommendation_endpoint(
    payload: RecommendationCreate,
    db: Session = Depends(get_db),
):
    """Ingest a new AI/Risk recommendation (status: PENDING)."""
    station = db.query(Station).filter(Station.id == payload.station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station ID {payload.station_id} not found",
        )
    rec = create_recommendation(payload, db)
    return SuccessResponse(
        message=f"Recommendation ID {rec.id} created successfully",
        data=_serialize_rec(rec),
    )


@router.get("/{station_id}", response_model=SuccessResponse)
def get_recommendations_endpoint(
    station_id: str,
    status: Optional[str] = Query(None, description="Filter by status: PENDING, APPROVED, MODIFIED, REJECTED"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve recommendations for a station. Accessible to all authenticated roles (VIEWER, CONTROLLER, ADMIN)."""
    station = _resolve_station(station_id, db)
    recs = get_station_recommendations(station.id, status, db)
    return SuccessResponse(data=[_serialize_rec(r) for r in recs])


@router.post("/{id}/approve", response_model=SuccessResponse)
def approve_recommendation_endpoint(
    id: int,
    payload: Optional[RecommendationApproveRequest] = None,
    current_user: User = Depends(require_role([UserRole.CONTROLLER, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Approve a recommendation. Accessible only to CONTROLLER and ADMIN."""
    rec = approve_recommendation(id, current_user, payload, db)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation ID {id} not found",
        )
    return SuccessResponse(
        message=f"Recommendation {id} APPROVED by {current_user.username}",
        data=_serialize_rec(rec),
    )


@router.post("/{id}/modify", response_model=SuccessResponse)
def modify_recommendation_endpoint(
    id: int,
    payload: RecommendationModifyRequest,
    current_user: User = Depends(require_role([UserRole.CONTROLLER, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Modify recommendation action. Accessible only to CONTROLLER and ADMIN."""
    rec = modify_recommendation(id, current_user, payload, db)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation ID {id} not found",
        )
    return SuccessResponse(
        message=f"Recommendation {id} MODIFIED by {current_user.username}",
        data=_serialize_rec(rec),
    )


@router.post("/{id}/reject", response_model=SuccessResponse)
def reject_recommendation_endpoint(
    id: int,
    payload: RecommendationRejectRequest,
    current_user: User = Depends(require_role([UserRole.CONTROLLER, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Reject a recommendation. Accessible only to CONTROLLER and ADMIN."""
    rec = reject_recommendation(id, current_user, payload, db)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation ID {id} not found",
        )
    return SuccessResponse(
        message=f"Recommendation {id} REJECTED by {current_user.username}",
        data=_serialize_rec(rec),
    )

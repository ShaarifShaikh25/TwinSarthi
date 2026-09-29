"""api/routes/alerts.py

Alerts REST API Endpoints:
- GET /api/alerts/{station_id} -> list alerts for a station (supports status, severity filters)
- POST /api/alerts/{alert_id}/acknowledge -> transition alert to ACKNOWLEDGED
- POST /api/alerts/{alert_id}/resolve -> transition alert to RESOLVED
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas import SuccessResponse
from app.models.station import Station
from app.services.alert_service import (
    get_station_alerts,
    acknowledge_alert,
    resolve_alert,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Alerts"])


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


@router.get("/{station_id}", response_model=SuccessResponse)
def get_alerts_endpoint(
    station_id: str,
    status: Optional[str] = Query(None, description="Filter by alert status: active, acknowledged, resolved"),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical"),
    db: Session = Depends(get_db),
):
    """Retrieve all alerts for a given station (by station ID or code), with optional status and severity filters."""
    station = _resolve_station(station_id, db)
    alerts = get_station_alerts(
        station_id=station.id,
        status_filter=status,
        severity_filter=severity,
        db=db,
    )
    data = [
        {
            "id": a.id,
            "station_id": a.station_id,
            "station_code": station.code,
            "severity": a.severity.value if hasattr(a.severity, "value") else str(a.severity),
            "type": a.type,
            "message": a.message,
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        }
        for a in alerts
    ]
    return SuccessResponse(data=data)


@router.post("/{alert_id}/acknowledge", response_model=SuccessResponse)
def acknowledge_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
):
    """Acknowledge an ongoing alert."""
    alert = acknowledge_alert(alert_id, db)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert ID {alert_id} not found",
        )
    return SuccessResponse(
        message=f"Alert {alert_id} acknowledged successfully",
        data={
            "id": alert.id,
            "station_id": alert.station_id,
            "status": alert.status.value if hasattr(alert.status, "value") else str(alert.status),
            "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
        },
    )


@router.post("/{alert_id}/resolve", response_model=SuccessResponse)
def resolve_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
):
    """Resolve an alert."""
    alert = resolve_alert(alert_id, db)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert ID {alert_id} not found",
        )
    return SuccessResponse(
        message=f"Alert {alert_id} resolved successfully",
        data={
            "id": alert.id,
            "station_id": alert.station_id,
            "status": alert.status.value if hasattr(alert.status, "value") else str(alert.status),
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        },
    )

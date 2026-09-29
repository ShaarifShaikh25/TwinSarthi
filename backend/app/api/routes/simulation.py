"""app/api/routes/simulation.py

Simulation API Endpoints:
- POST /api/simulation/run: Execute digital twin scenario simulation
Protected by RBAC: Requires CONTROLLER or ADMIN role. VIEWER role is rejected with 403 Forbidden.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role
from app.models.user import User, UserRole
from app.models.station import Station
from app.schemas.simulation import SimulationRequest, SimulationResult
from app.schemas import SuccessResponse
from app.services.simulation_service import run_simulation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Simulation"])


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


@router.post("/run", response_model=SuccessResponse)
def run_simulation_endpoint(
    request: SimulationRequest,
    current_user: User = Depends(require_role([UserRole.CONTROLLER, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Execute scenario simulation for Maitri / Bharati stations.
    Accessible only to CONTROLLER and ADMIN roles.
    """
    # Verify station exists
    station = _resolve_station(request.station_id, db)
    # Ensure request carries resolved station code
    request.station_id = station.code

    result: SimulationResult = run_simulation(request, current_user)
    return SuccessResponse(
        message=f"Simulation '{result.simulation_id}' executed successfully for station {station.code}",
        data=result.model_dump(),
    )

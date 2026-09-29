"""app/api/routes/intelligence.py

AI, Risk, Simulation, and Optimization API Endpoints (Phase 9):
- POST /api/intelligence/energy/predict
- POST /api/intelligence/fuel/predict
- POST /api/intelligence/anomalies/detect
- POST /api/intelligence/risk/calculate (USP 1: Cascading Risk Graph)
- POST /api/intelligence/simulation/what-if (USP 2: What-If Simulation)
- POST /api/intelligence/resupply/optimize (USP 5: Resupply Priority Matrix)
"""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas import SuccessResponse
from app.schemas.intelligence import (
    EnergyPredictionRequest,
    EnergyPredictionResult,
    FuelPredictionRequest,
    FuelPredictionResult,
    AnomalyDetectionRequest,
    AnomalyDetectionResult,
    RiskCalculationRequest,
    RiskAssessmentResult,
    WhatIfSimulationRequest,
    WhatIfSimulationResult,
    ResupplyOptimizationRequest,
    ResupplyOptimizationResult,
)
from app.services.intelligence import (
    predict_energy as svc_predict_energy,
    predict_fuel as svc_predict_fuel,
    detect_anomaly as svc_detect_anomaly,
    calculate_risk as svc_calculate_risk,
    run_simulation as svc_run_simulation,
    optimize_resupply as svc_optimize_resupply,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI / Risk / Simulation Intelligence"])


@router.post("/energy/predict", response_model=SuccessResponse)
def predict_energy_endpoint(
    request: EnergyPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Predict electrical and thermal power demand profile."""
    result: EnergyPredictionResult = svc_predict_energy(request, db)
    return SuccessResponse(
        message=f"Energy forecast generated for station {result.station_id} ({result.horizon_hours}h horizon)",
        data=result.model_dump(),
    )


@router.post("/fuel/predict", response_model=SuccessResponse)
def predict_fuel_endpoint(
    request: FuelPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Predict fuel burn trajectory and calculate days of autonomy."""
    result: FuelPredictionResult = svc_predict_fuel(request, db)
    return SuccessResponse(
        message=f"Fuel autonomy forecast generated for station {result.station_id}: {result.days_of_autonomy} days remaining",
        data=result.model_dump(),
    )


@router.post("/anomalies/detect", response_model=SuccessResponse)
def detect_anomalies_endpoint(
    request: AnomalyDetectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Scan sensor telemetry streams for multivariate operational anomalies."""
    result: AnomalyDetectionResult = svc_detect_anomaly(request, db)
    return SuccessResponse(
        message=f"Anomaly scan completed for station {result.station_id}: {result.total_anomalies_detected} anomalies detected",
        data=result.model_dump(),
    )


@router.post("/risk/calculate", response_model=SuccessResponse)
def calculate_risk_endpoint(
    request: RiskCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate operational risk and evaluate cascading failure pathways (USP 1)."""
    result: RiskAssessmentResult = svc_calculate_risk(request, db)
    return SuccessResponse(
        message=f"Risk assessment computed: {result.risk_level} ({result.risk_type})",
        data=result.model_dump(),
    )


@router.post("/simulation/what-if", response_model=SuccessResponse)
def run_what_if_simulation_endpoint(
    request: WhatIfSimulationRequest,
    current_user: User = Depends(require_role([UserRole.CONTROLLER, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Execute what-if polar survival simulation (USP 2). Requires CONTROLLER or ADMIN role."""
    result: WhatIfSimulationResult = svc_run_simulation(request, current_user.username, db)
    return SuccessResponse(
        message=f"What-if simulation '{result.simulation_id}' completed (Survivability: {result.survivability_score})",
        data=result.model_dump(),
    )


@router.post("/resupply/optimize", response_model=SuccessResponse)
def optimize_resupply_endpoint(
    request: ResupplyOptimizationRequest,
    current_user: User = Depends(require_role([UserRole.CONTROLLER, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Compute optimal icebreaker resupply window and cargo priority matrix (USP 5). Requires CONTROLLER or ADMIN role."""
    result: ResupplyOptimizationResult = svc_optimize_resupply(request, db)
    return SuccessResponse(
        message=f"Optimal resupply window scheduled for {result.optimal_delivery_date}",
        data=result.model_dump(),
    )

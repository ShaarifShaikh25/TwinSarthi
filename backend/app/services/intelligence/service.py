"""app/services/intelligence/service.py

POLAR-TWIN Intelligence Service Coordinator & Pluggable Provider Registry.

Architecture:
API Route
    ↓
Service Interface (this module)
    ↓
Developer 3 Intelligence Provider (BaseIntelligenceProvider)
    ↓
Backend Result
    ↓
Database Persistence (RiskRecord, SimulationRecord, ResupplyPlanRecord, Recommendation)
    ↓
WebSocket Broadcast (/ws/{station_id})
    ↓
Frontend Real-Time Operators
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.station import Station
from app.models.intelligence import RiskRecord, SimulationRecord, ResupplyPlanRecord
from app.models.recommendation import Recommendation, RecommendationSeverity, RecommendationStatus, RecommendationAudit
from app.schemas.intelligence import (
    TwinContext,
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
from app.services.intelligence.base import BaseIntelligenceProvider
from app.services.intelligence.fallback_provider import FallbackIntelligenceProvider
from app.services.intelligence.context import build_twin_context
from app.websockets.manager import ws_manager

logger = logging.getLogger(__name__)

# Singleton active intelligence provider (defaults to FallbackIntelligenceProvider)
_active_provider: BaseIntelligenceProvider = FallbackIntelligenceProvider()


def register_intelligence_provider(provider: BaseIntelligenceProvider) -> None:
    """Dependency injection hook allowing Developer 3 to register their custom ML/AI provider."""
    global _active_provider
    if not isinstance(provider, BaseIntelligenceProvider):
        raise TypeError("Provider must implement BaseIntelligenceProvider interface")
    _active_provider = provider
    logger.info("Registered custom AI Intelligence Provider: %s", provider.__class__.__name__)


def get_intelligence_provider() -> BaseIntelligenceProvider:
    """Retrieve currently active intelligence provider."""
    return _active_provider


def _resolve_station(station_id: str, db: Session) -> Station:
    """Resolve station by integer ID or uppercase/lowercase station code."""
    norm = station_id.strip()
    if norm.isdigit():
        st = db.query(Station).filter(Station.id == int(norm)).first()
        if st:
            return st
    st = db.query(Station).filter(Station.code.ilike(norm)).first()
    if not st:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station '{station_id}' not found",
        )
    return st


def _safe_ws_broadcast(coro):
    """Safely schedule an async WebSocket broadcast from sync or async context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)
    except Exception as exc:
        logger.error("Failed to broadcast WebSocket intelligence event: %s", exc)


# ============================================================================
# Core Intelligence Interfaces
# ============================================================================

def predict_energy(
    request: EnergyPredictionRequest,
    db: Session,
) -> EnergyPredictionResult:
    """1. Predict energy demand profile over forecast horizon."""
    station = _resolve_station(request.station_id, db)
    context = build_twin_context(station, db)
    provider = get_intelligence_provider()
    result = provider.predict_energy(context, request)
    return result


def predict_fuel(
    request: FuelPredictionRequest,
    db: Session,
) -> FuelPredictionResult:
    """2. Predict fuel consumption trajectory and days of autonomy."""
    station = _resolve_station(request.station_id, db)
    context = build_twin_context(station, db)
    provider = get_intelligence_provider()
    result = provider.predict_fuel(context, request)

    # If fuel risk is high or critical, broadcast WebSocket alert & risk update
    if result.risk_level in ("HIGH", "CRITICAL"):
        event = {
            "type": "risk_update",
            "station_id": station.code.lower(),
            "risk_level": result.risk_level,
            "risk_type": "FUEL_AUTONOMY",
            "reason": f"Projected days of autonomy depleted to {result.days_of_autonomy} days",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _safe_ws_broadcast(ws_manager.broadcast_to_station(station.code.lower(), event))

    return result


def detect_anomaly(
    request: AnomalyDetectionRequest,
    db: Session,
) -> AnomalyDetectionResult:
    """3. Detect multivariate telemetry anomalies across sensors."""
    station = _resolve_station(request.station_id, db)
    context = build_twin_context(station, db)
    provider = get_intelligence_provider()
    result = provider.detect_anomaly(context, request)
    return result


def calculate_risk(
    request: RiskCalculationRequest,
    db: Session,
) -> RiskAssessmentResult:
    """4. Calculate operational risk score and trace cascading failure paths (USP 1).
    Persists risk assessment to database and broadcasts real-time risk updates.
    """
    station = _resolve_station(request.station_id, db)
    context = build_twin_context(station, db)
    provider = get_intelligence_provider()
    result = provider.calculate_risk(context, request)

    # 1. Persist in database
    cascading_data = [c.model_dump() for c in result.cascading_pathways]
    record = RiskRecord(
        station_id=station.id,
        risk_level=result.risk_level,
        risk_type=result.risk_type,
        reason=result.reason,
        affected_systems=result.affected_systems,
        cascading_pathways=cascading_data,
        recommended_action=result.recommended_action,
        confidence=result.confidence,
    )
    db.add(record)
    db.commit()

    # 2. If action recommended and risk elevated, create a PENDING recommendation for controller review
    if result.risk_level in ("HIGH", "CRITICAL") and result.recommended_action:
        rec = Recommendation(
            station_id=station.id,
            type=result.risk_type.lower(),
            severity=RecommendationSeverity.HIGH if result.risk_level == "HIGH" else RecommendationSeverity.CRITICAL,
            title=f"Mitigate {result.risk_type} Cascading Risk",
            reason=result.reason,
            recommended_action=result.recommended_action,
            confidence=result.confidence,
            status=RecommendationStatus.PENDING,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

        # Audit entry
        audit = RecommendationAudit(
            recommendation_id=rec.id,
            user_id=None,
            action="CREATED",
            new_status=RecommendationStatus.PENDING.value,
            notes=f"Auto-generated by AI Cascading Risk engine (Confidence: {result.confidence})",
        )
        db.add(audit)
        db.commit()

    # 3. Broadcast real-time WebSocket update
    risk_event = {
        "type": "risk_update",
        "station_id": station.code.lower(),
        "risk_level": result.risk_level,
        "risk_type": result.risk_type,
        "affected_systems": result.affected_systems,
        "reason": result.reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _safe_ws_broadcast(ws_manager.broadcast_to_station(station.code.lower(), risk_event))

    return result


def run_simulation(
    request: WhatIfSimulationRequest,
    user_name: str,
    db: Session,
) -> WhatIfSimulationResult:
    """5. Execute what-if polar survival simulation (USP 2).
    Persists simulation record in database.
    """
    station = _resolve_station(request.station_id, db)
    context = build_twin_context(station, db)
    provider = get_intelligence_provider()
    result = provider.run_simulation(context, request)

    # Persist simulation record
    sim_record = SimulationRecord(
        simulation_id=result.simulation_id,
        station_id=station.id,
        scenario_type=result.scenario_type,
        duration_hours=result.duration_hours,
        survivability_score=result.survivability_score,
        summary=result.summary,
        metrics=result.metrics,
        critical_events=result.critical_events,
        recommended_contingencies=result.contingencies,
        executed_by=user_name,
    )
    db.add(sim_record)
    db.commit()

    return result


def optimize_resupply(
    request: ResupplyOptimizationRequest,
    db: Session,
) -> ResupplyOptimizationResult:
    """6. Compute optimal icebreaker resupply window and cargo priorities (USP 5).
    Persists resupply plan proposal in database.
    """
    station = _resolve_station(request.station_id, db)
    context = build_twin_context(station, db)
    provider = get_intelligence_provider()
    result = provider.optimize_resupply(context, request)

    # Persist resupply plan
    cargo_json = [c.model_dump() for c in result.cargo_priorities]
    plan_record = ResupplyPlanRecord(
        station_id=station.id,
        optimal_resupply_date=result.optimal_delivery_date,
        planning_horizon_days=result.planning_horizon_days,
        cargo_priorities=cargo_json,
        required_volume_m3=result.total_cargo_volume_m3,
        risk_if_delayed=result.risk_if_delayed,
        status="PROPOSED",
        notes=result.operational_notes,
    )
    db.add(plan_record)
    db.commit()

    return result

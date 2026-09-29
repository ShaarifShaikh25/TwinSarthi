"""app/services/simulation_service.py

POLAR-TWIN Simulation Interface:
- Clean service contract for executing scenario simulations
- Provides baseline deterministic simulations for operational demonstration
- Prepared for Developer 3 (ML / Causal Digital Twin Lead) to plug in physics-informed
  neural networks, causal Bayesian networks, and predictive anomaly models.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.models.user import User
from app.schemas.simulation import SimulationRequest, SimulationResult

logger = logging.getLogger(__name__)


def run_simulation(
    request: SimulationRequest,
    user: User,
) -> SimulationResult:
    """Execute scenario simulation for Maitri / Bharati digital twin.

    ===========================================================================
    NOTE FOR DEVELOPER 3 (ML / CAUSAL TWIN ENGINEER):
    Replace the stubbed calculations below with your ML inference, causal DAG
    evaluations, or thermodynamic / energy forecasting models.
    The method signature and SimulationResult contract must remain invariant.
    ===========================================================================
    """
    sim_id = f"sim-{uuid.uuid4().hex[:10]}"
    station_norm = request.station_id.upper()
    scenario = request.scenario_type.lower()
    horizon = request.duration_hours
    user_name = user.username if user else "system"
    now = datetime.now(timezone.utc)

    logger.info(
        "Initiating simulation '%s' (scenario: %s, duration: %dh) on %s by user %s",
        sim_id,
        scenario,
        horizon,
        station_norm,
        user_name,
    )

    # Deterministic scenario results for demonstration & testing
    if "blizzard" in scenario:
        summary = f"Simulated severe polar blizzard over {horizon}h horizon. Station life support remains secure with load shedding."
        metrics = {
            "predicted_min_temp_c": -58.4,
            "predicted_max_wind_ms": 48.2,
            "fuel_depletion_rate_pct_per_day": 3.8,
            "thermal_loss_rate_kw": 42.5,
            "risk_index": 0.78,
            "power_grid_stability": "STABLE_ON_EMERGENCY",
        }
        recs = [
            {
                "type": "thermal_preservation",
                "recommended_action": "Seal non-essential science annex corridors and lower HVAC setpoint by 2°C.",
                "confidence": 0.91,
            },
            {
                "type": "energy_management",
                "recommended_action": "Switch Secondary Generator to warm standby; maintain primary at 78% load.",
                "confidence": 0.88,
            },
        ]
    elif "generator" in scenario or "power" in scenario:
        summary = f"Simulated primary generator trip scenario over {horizon}h horizon. Backup auto-start initiated within 15 seconds."
        metrics = {
            "backup_generator_readiness_pct": 100.0,
            "switchover_time_seconds": 12.4,
            "unserved_energy_kwh": 0.0,
            "critical_life_support_uptime_pct": 100.0,
            "risk_index": 0.45,
            "power_grid_stability": "NOMINAL",
        }
        recs = [
            {
                "type": "maintenance_action",
                "recommended_action": "Inspect exciter coil and replace auxiliary fuel pump filter on Generator 1.",
                "confidence": 0.85,
            }
        ]
    elif "fuel" in scenario:
        summary = f"Simulated strategic fuel conservation across {horizon}h. Reserve autonomy extended by 18 days."
        metrics = {
            "projected_fuel_savings_liters": 1420.0,
            "station_autonomy_days": 64.5,
            "risk_index": 0.28,
            "power_grid_stability": "OPTIMIZED",
        }
        recs = [
            {
                "type": "fuel_optimization",
                "recommended_action": "Synchronize thermal recovery loop with snow-melter to conserve 120L diesel/day.",
                "confidence": 0.93,
            }
        ]
    else:
        summary = f"Generic baseline operational simulation over {horizon}h on station {station_norm}."
        metrics = {
            "energy_efficiency_score": 88.5,
            "equipment_wear_rate_index": 0.04,
            "risk_index": 0.22,
            "overall_health": "OPTIMAL",
        }
        recs = [
            {
                "type": "general_optimization",
                "recommended_action": "Maintain scheduled routine sensor calibrations and baseline telemetry stream.",
                "confidence": 0.82,
            }
        ]

    return SimulationResult(
        simulation_id=sim_id,
        station_id=station_norm,
        scenario_type=scenario,
        status="COMPLETED",
        duration_hours=horizon,
        summary=summary,
        metrics=metrics,
        generated_recommendations=recs,
        executed_by=user_name,
        timestamp=now,
    )

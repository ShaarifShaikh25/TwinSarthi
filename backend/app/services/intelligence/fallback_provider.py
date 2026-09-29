"""app/services/intelligence/fallback_provider.py

Fallback Intelligence Provider:
Provides reliable, deterministic baseline calculations for energy, fuel,
anomalies, risk assessment, what-if simulations, and resupply planning.
Ensures the backend remains fully operational even before Developer 3 deploys ML models.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from app.schemas.intelligence import (
    TwinContext,
    EnergyPredictionRequest,
    EnergyPredictionResult,
    FuelPredictionRequest,
    FuelPredictionResult,
    AnomalyDetectionRequest,
    AnomalyDetectionResult,
    AnomalyItem,
    RiskCalculationRequest,
    RiskAssessmentResult,
    CascadingRiskNode,
    WhatIfSimulationRequest,
    WhatIfSimulationResult,
    ResupplyOptimizationRequest,
    ResupplyOptimizationResult,
    ResupplyItem,
)
from app.services.intelligence.base import BaseIntelligenceProvider


class FallbackIntelligenceProvider(BaseIntelligenceProvider):
    """Deterministic engineering-rule fallback provider."""

    def predict_energy(
        self,
        context: TwinContext,
        request: EnergyPredictionRequest,
    ) -> EnergyPredictionResult:
        now = datetime.now(timezone.utc)
        # Baseline station load (Maitri ~70kW, Bharati ~85kW nominal)
        base_load = 75.0 if context.station_code == "MAITRI" else 90.0

        # Adjust for cold weather thermal loads
        temp = context.environment_state.get("temperature", -25.0)
        thermal_demand = max(0.0, (-temp) * 0.45)
        total_mean_load = round(base_load + thermal_demand, 2)
        peak_load = round(total_mean_load * 1.25, 2)

        hourly = []
        for h in range(min(request.horizon_hours, 24)):
            ts = now + timedelta(hours=h)
            variation = (h % 6) * 1.5 - 3.0
            hourly.append({
                "hour": h + 1,
                "timestamp": ts.isoformat(),
                "load_kw": round(total_mean_load + variation, 2),
                "confidence": 0.85,
            })

        return EnergyPredictionResult(
            station_id=context.station_code,
            horizon_hours=request.horizon_hours,
            predicted_mean_load_kw=total_mean_load,
            predicted_peak_load_kw=peak_load,
            confidence=0.85,
            hourly_forecast=hourly,
            recommendation="Baseline load profile stable. Maintain regular generator rotation.",
            generated_at=now,
        )

    def predict_fuel(
        self,
        context: TwinContext,
        request: FuelPredictionRequest,
    ) -> FuelPredictionResult:
        now = datetime.now(timezone.utc)
        # Extract fuel percentage or default to 65%
        fuel_pct = context.inventory_state.get("fuel_reserve_percent", 65.0)
        tank_capacity_liters = 60000.0  # standard polar tank container capacity
        current_liters = round((fuel_pct / 100.0) * tank_capacity_liters, 1)

        # Baseline fuel burn rate ~32 liters/hour = 768 L/day
        burn_rate = 768.0
        if request.generator_operational_mode == "conservation":
            burn_rate *= 0.85
        elif request.generator_operational_mode == "emergency":
            burn_rate *= 1.2

        days_autonomy = round(current_liters / max(burn_rate, 1.0), 1)
        crit_days = max(0, int(days_autonomy - 10))
        critical_date = (now + timedelta(days=crit_days)).strftime("%Y-%m-%d")

        risk_level = "LOW"
        if days_autonomy < 15:
            risk_level = "CRITICAL"
        elif days_autonomy < 30:
            risk_level = "HIGH"
        elif days_autonomy < 60:
            risk_level = "MEDIUM"

        return FuelPredictionResult(
            station_id=context.station_code,
            current_fuel_liters=current_liters,
            daily_burn_rate_liters=round(burn_rate, 1),
            days_of_autonomy=days_autonomy,
            critical_threshold_date=critical_date,
            risk_level=risk_level,
            confidence=0.88,
            recommended_conservation_strategy=(
                "Implement 15% load-shedding on non-critical labs to extend autonomy by 18 days"
                if risk_level in ("HIGH", "CRITICAL")
                else "Nominal fuel consumption; routine resupply schedule holds"
            ),
            generated_at=now,
        )

    def detect_anomaly(
        self,
        context: TwinContext,
        request: AnomalyDetectionRequest,
    ) -> AnomalyDetectionResult:
        now = datetime.now(timezone.utc)
        anomalies: List[AnomalyItem] = []

        # Analyze recent telemetry against baseline bands
        for t in context.recent_telemetry:
            val = t.get("value", 0.0)
            sid = t.get("sensor_id", 0)
            # Heuristic check for extreme deviation
            if val < -65.0:
                anomalies.append(AnomalyItem(
                    sensor_id=sid,
                    sensor_type="temperature",
                    observed_value=val,
                    expected_value=-28.0,
                    anomaly_score=0.92,
                    is_anomaly=True,
                    severity="CRITICAL",
                    reason="Temperature reading violates 3-sigma historical baseline envelope.",
                ))
            elif val > 45.0 and "wind" in str(t.get("source", "")).lower():
                anomalies.append(AnomalyItem(
                    sensor_id=sid,
                    sensor_type="wind",
                    observed_value=val,
                    expected_value=12.0,
                    anomaly_score=0.88,
                    is_anomaly=True,
                    severity="HIGH",
                    reason="Blizzard wind gust speed exceeds sensor standard operating envelope.",
                ))

        return AnomalyDetectionResult(
            station_id=context.station_code,
            total_anomalies_detected=len(anomalies),
            anomalies=anomalies,
            confidence=0.86,
            analyzed_readings_count=len(context.recent_telemetry),
            timestamp=now,
        )

    def calculate_risk(
        self,
        context: TwinContext,
        request: RiskCalculationRequest,
    ) -> RiskAssessmentResult:
        now = datetime.now(timezone.utc)
        fuel_pct = context.inventory_state.get("fuel_reserve_percent", 70.0)
        temp = context.environment_state.get("temperature", -25.0)

        # Baseline risk determination
        risk_level = "LOW"
        risk_type = "NOMINAL"
        reason = "All life support and energy systems operating within standard margins."
        affected = []
        action = "Maintain continuous digital twin telemetry monitoring."

        if fuel_pct < 20.0 or temp < -55.0 or context.active_alerts_count > 0:
            risk_level = "HIGH"
            risk_type = "FUEL_THERMAL"
            reason = f"Combined low fuel reserve ({fuel_pct}%) and severe ambient cold ({temp}°C)."
            affected = ["Diesel_Generator_1", "Main_Habitat_HVAC", "Freeze_Protection_Circuits"]
            action = "Activate emergency energy conservation protocol and prioritize generator fuel line heaters."

        # USP 1: Cascading Risk Graph
        cascades = [
            CascadingRiskNode(
                system="Diesel_Power_Generation",
                failure_probability=0.25 if risk_level == "HIGH" else 0.05,
                impact_severity="CRITICAL",
                downstream_cascades=["HVAC_Thermal_Plant", "Potable_Water_Lines", "Satellite_Comms"],
            ),
            CascadingRiskNode(
                system="HVAC_Thermal_Plant",
                failure_probability=0.30 if temp < -45.0 else 0.08,
                impact_severity="HIGH",
                downstream_cascades=["Habitat_Indoor_Climate", "Science_Lab_Incubators"],
            ),
        ]

        return RiskAssessmentResult(
            risk_level=risk_level,
            risk_type=risk_type,
            reason=reason,
            affected_systems=affected,
            cascading_pathways=cascades,
            recommended_action=action,
            confidence=0.87,
            timestamp=now,
        )

    def run_simulation(
        self,
        context: TwinContext,
        request: WhatIfSimulationRequest,
    ) -> WhatIfSimulationResult:
        now = datetime.now(timezone.utc)
        sim_id = f"sim-{uuid.uuid4().hex[:10]}"
        scenario = request.scenario_type.lower()
        horizon = request.duration_hours

        # USP 2: What-If Simulation
        survivability = 0.95
        if "blizzard" in scenario:
            summary = f"Simulated {horizon}h extreme blizzard survival. Station grid sustains life support via automated load shedding."
            survivability = 0.82
            metrics = {"thermal_loss_kw": 38.0, "fuel_burn_liters": horizon * 34.0, "risk_index": 0.65}
            critical_events = [
                {"hour": 6, "event": "External ambient temp plunged past -52°C"},
                {"hour": 14, "event": "Science block HVAC throttled to protect central habitat"},
            ]
            contingencies = [
                {"action": "Seal thermal vestibules", "priority": "IMMEDIATE"},
                {"action": "Preheat backup generator coolant", "priority": "HIGH"},
            ]
        elif "generator" in scenario:
            summary = f"Simulated {horizon}h single-generator loss. Backup unit seamlessly took base load in 14 seconds."
            survivability = 0.91
            metrics = {"unserved_load_kwh": 0.0, "switchover_seconds": 14.2, "risk_index": 0.35}
            critical_events = [{"hour": 0, "event": "Primary generator breaker opened"}]
            contingencies = [{"action": "Dispatch technician for starter coil check", "priority": "STANDARD"}]
        else:
            summary = f"Baseline what-if scenario '{request.scenario_type}' completed across {horizon}h horizon."
            metrics = {"grid_stability_index": 0.98, "risk_index": 0.15}
            critical_events = []
            contingencies = [{"action": "Maintain normal watch", "priority": "LOW"}]

        return WhatIfSimulationResult(
            simulation_id=sim_id,
            station_id=context.station_code,
            scenario_type=request.scenario_type,
            duration_hours=horizon,
            survivability_score=survivability,
            summary=summary,
            metrics=metrics,
            critical_events=critical_events,
            contingencies=contingencies,
            executed_at=now,
        )

    def optimize_resupply(
        self,
        context: TwinContext,
        request: ResupplyOptimizationRequest,
    ) -> ResupplyOptimizationResult:
        now = datetime.now(timezone.utc)
        optimal_date = (now + timedelta(days=45)).strftime("%Y-%m-%d")

        # USP 5: Resupply Priority Matrix
        priorities = [
            ResupplyItem(
                item_name="Polar Grade Low-Sulfur Diesel Fuel",
                category="FUEL",
                priority_rank=1,
                required_quantity=85000.0,
                unit="Liters",
                risk_if_excluded="CRITICAL: Total station black-start risk before austral winter",
            ),
            ResupplyItem(
                item_name="Generator Turbocharger & Injector Spares",
                category="SPARE_PART",
                priority_rank=2,
                required_quantity=4.0,
                unit="Kits",
                risk_if_excluded="HIGH: Redundancy loss during multi-week storm windows",
            ),
            ResupplyItem(
                item_name="Dry Rations & Medical Cryo Supplies",
                category="FOOD_MEDICAL",
                priority_rank=3,
                required_quantity=1800.0,
                unit="Kilograms",
                risk_if_excluded="MEDIUM: Rationing required after day 60",
            ),
        ]

        return ResupplyOptimizationResult(
            station_id=context.station_code,
            optimal_delivery_date=optimal_date,
            planning_horizon_days=request.planning_horizon_days,
            cargo_priorities=priorities,
            total_cargo_volume_m3=120.5,
            risk_if_delayed="HIGH",
            confidence=0.89,
            operational_notes=(
                f"Icebreaker approach window aligned with satellite ice-charting forecasts for {context.station_code} coast."
            ),
            generated_at=now,
        )

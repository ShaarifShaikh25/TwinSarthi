"""app/schemas/intelligence.py

POLAR-TWIN AI, Risk, Simulation, and Optimization Data Contracts (Phase 9).
Provides strictly-typed request and response structures for:
1. predict_energy()
2. predict_fuel()
3. detect_anomaly()
4. calculate_risk() (including Cascading Risk - USP 1)
5. run_simulation() (What-If Scenarios - USP 2)
6. optimize_resupply() (Resupply Priority Matrix - USP 5)
Plus Mission Continuity & Constraint-Aware Replanning (USPs 3 & 4).
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Context Aggregator: Input to Intelligence Modules
# ============================================================================

class TwinContext(BaseModel):
    """Unified operational state supplied to Developer 3 intelligence modules."""
    station_id: int
    station_code: str
    latitude: float
    longitude: float
    digital_twin_state: Dict[str, Any]
    environment_state: Dict[str, Any]
    energy_state: Dict[str, Any]
    inventory_state: Dict[str, Any]
    equipment_state: List[Dict[str, Any]]
    recent_telemetry: List[Dict[str, Any]]
    active_alerts_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 1. predict_energy()
# ============================================================================

class EnergyPredictionRequest(BaseModel):
    station_id: str = Field(..., description="Station ID or code (MAITRI/BHARATI)")
    horizon_hours: int = Field(default=24, ge=1, le=168, description="Forecast horizon in hours")
    include_renewable_blend: bool = Field(default=True, description="Consider solar/wind generation")


class EnergyPredictionResult(BaseModel):
    station_id: str
    horizon_hours: int
    predicted_mean_load_kw: float
    predicted_peak_load_kw: float
    confidence: float = Field(ge=0.0, le=1.0)
    hourly_forecast: List[Dict[str, Any]]
    recommendation: Optional[str] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 2. predict_fuel()
# ============================================================================

class FuelPredictionRequest(BaseModel):
    station_id: str = Field(..., description="Station ID or code")
    horizon_days: int = Field(default=30, ge=1, le=365, description="Projection duration in days")
    generator_operational_mode: str = Field(default="nominal", description="nominal, conservation, or emergency")


class FuelPredictionResult(BaseModel):
    station_id: str
    current_fuel_liters: float
    daily_burn_rate_liters: float
    days_of_autonomy: float
    critical_threshold_date: Optional[str] = None
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_conservation_strategy: Optional[str] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 3. detect_anomaly()
# ============================================================================

class AnomalyDetectionRequest(BaseModel):
    station_id: str = Field(..., description="Station ID or code")
    window_hours: int = Field(default=24, ge=1, le=72, description="Telemetry analysis window in hours")
    sensitivity: float = Field(default=0.85, ge=0.1, le=1.0, description="Detection sensitivity threshold")


class AnomalyItem(BaseModel):
    sensor_id: int
    sensor_type: str
    observed_value: float
    expected_value: float
    anomaly_score: float = Field(ge=0.0, le=1.0)
    is_anomaly: bool
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str


class AnomalyDetectionResult(BaseModel):
    station_id: str
    total_anomalies_detected: int
    anomalies: List[AnomalyItem]
    confidence: float
    analyzed_readings_count: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 4. calculate_risk() [POLAR-TWIN USP 1: Cascading Risk Graph]
# ============================================================================

class RiskCalculationRequest(BaseModel):
    station_id: str = Field(..., description="Station ID or code")
    include_cascading: bool = Field(default=True, description="Evaluate cascading failure chains")


class CascadingRiskNode(BaseModel):
    system: str  # e.g. Diesel_Generator_1, HVAC_Heating_Loop, Potable_Water_Lines
    failure_probability: float = Field(ge=0.0, le=1.0)
    impact_severity: str
    downstream_cascades: List[str]  # Affected downstream nodes in the causal DAG


class RiskAssessmentResult(BaseModel):
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    risk_type: str  # FUEL, THERMAL, POWER, STRUCTURAL, LOGISTICS
    reason: str
    affected_systems: List[str]
    cascading_pathways: List[CascadingRiskNode]
    recommended_action: str
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 5. run_simulation() [POLAR-TWIN USP 2: What-If Simulation]
# ============================================================================

class WhatIfSimulationRequest(BaseModel):
    station_id: str = Field(..., description="Station ID or code")
    scenario_type: str = Field(..., description="e.g. blizzard_survival, generator_outage, fuel_leak")
    duration_hours: int = Field(default=48, ge=1, le=720)
    perturbations: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Injected stress variables")


class WhatIfSimulationResult(BaseModel):
    simulation_id: str
    station_id: str
    scenario_type: str
    duration_hours: int
    survivability_score: float = Field(ge=0.0, le=1.0, description="1.0 = full continuity, <0.5 = compromised")
    summary: str
    metrics: Dict[str, Any]
    critical_events: List[Dict[str, Any]]
    contingencies: List[Dict[str, Any]]
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 6. optimize_resupply() [POLAR-TWIN USP 5: Resupply Optimization]
# ============================================================================

class ResupplyOptimizationRequest(BaseModel):
    station_id: str = Field(..., description="Station ID or code")
    planning_horizon_days: int = Field(default=90, ge=15, le=365)
    icebreaker_window_days: int = Field(default=14, description="Weather window duration for sea approach")


class ResupplyItem(BaseModel):
    item_name: str
    category: str  # FUEL, SPARE_PART, MEDICAL, FOOD
    priority_rank: int
    required_quantity: float
    unit: str
    risk_if_excluded: str


class ResupplyOptimizationResult(BaseModel):
    station_id: str
    optimal_delivery_date: str
    planning_horizon_days: int
    cargo_priorities: List[ResupplyItem]
    total_cargo_volume_m3: float
    risk_if_delayed: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float
    operational_notes: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Special Support: USPs 3 & 4 (Mission Continuity & Replanning)
# ============================================================================

class MissionContinuityAssessment(BaseModel):
    mission_status: str  # NOMINAL, DEGRADED, CRITICAL, ABORT_EVAC
    max_sustainable_days: float
    active_constraints: List[str]
    viability_index: float = Field(ge=0.0, le=1.0)
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ReplanningProposal(BaseModel):
    proposal_id: str
    target_goal: str
    adjusted_schedules: List[Dict[str, Any]]
    power_reduction_kw: float
    fuel_extension_days: float
    deferred_science_operations: List[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

"""tests/test_intelligence.py

Test suite for POLAR-TWIN Phase 9:
- AI / Risk / Simulation Integration Interfaces
- All 6 core intelligence functions:
  1. predict_energy()
  2. predict_fuel()
  3. detect_anomaly()
  4. calculate_risk() (including USP 1 Cascading Risk Graph)
  5. run_simulation() (including USP 2 What-If Scenarios)
  6. optimize_resupply() (including USP 5 Resupply Priority Matrix)
- Pluggable provider registry & dependency injection
- Fallback resilience (zero crashes when custom ML is absent)
- Role protection on simulation and resupply endpoints
"""

import pytest
from datetime import datetime, timezone
from starlette.testclient import TestClient

from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.station import Station, StationStatus
from app.models.equipment import Equipment, EquipmentStatus
from app.models.sensor import Sensor, SensorType, SensorStatus
from app.models.telemetry import Telemetry
from app.models.intelligence import RiskRecord, SimulationRecord, ResupplyPlanRecord
from app.models.recommendation import Recommendation
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
from app.services.intelligence import (
    register_intelligence_provider,
    get_intelligence_provider,
    BaseIntelligenceProvider,
    FallbackIntelligenceProvider,
    predict_energy,
    predict_fuel,
    detect_anomaly,
    calculate_risk,
    run_simulation,
    optimize_resupply,
)
from app.services.auth_service import seed_default_users

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema, test stations, equipment, sensors, and telemetry exist."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear relevant tables
    db.query(ResupplyPlanRecord).delete()
    db.query(SimulationRecord).delete()
    db.query(RiskRecord).delete()
    db.query(Recommendation).delete()
    db.query(Telemetry).delete()
    db.query(Sensor).delete()
    db.query(Equipment).delete()
    db.query(Station).delete()
    db.commit()

    # Seed MAITRI station
    maitri = Station(
        id=1,
        name="Maitri Research Station",
        code="MAITRI",
        latitude=-70.7667,
        longitude=11.7333,
        status=StationStatus.ACTIVE,
    )
    db.add(maitri)
    db.commit()

    # Seed equipment
    gen = Equipment(
        id=1,
        station_id=1,
        name="Primary Diesel Generator 1",
        type="generator",
        status=EquipmentStatus.OPERATIONAL,
        health_score=92.0,
    )
    db.add(gen)
    db.commit()

    # Seed sensors
    temp_sensor = Sensor(
        id=1,
        station_id=1,
        equipment_id=1,
        type=SensorType.TEMPERATURE,
        unit="°C",
        status=SensorStatus.ACTIVE,
    )
    fuel_sensor = Sensor(
        id=2,
        station_id=1,
        equipment_id=1,
        type=SensorType.FUEL_LEVEL,
        unit="%",
        status=SensorStatus.ACTIVE,
    )
    db.add_all([temp_sensor, fuel_sensor])
    db.commit()

    # Seed recent telemetry
    now = datetime.now(timezone.utc)
    t1 = Telemetry(sensor_id=1, value=-26.5, quality="GOOD", source="SIMULATED", timestamp=now)
    t2 = Telemetry(sensor_id=2, value=68.0, quality="GOOD", source="SIMULATED", timestamp=now)
    db.add_all([t1, t2])
    db.commit()

    # Seed default user accounts
    seed_default_users(db)
    # Ensure default fallback provider is reset
    register_intelligence_provider(FallbackIntelligenceProvider())
    db.close()


def _login(username: str, password: str) -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.json()["data"]["access_token"]


def test_predict_energy_service_and_api():
    """Verify predict_energy interface via service and REST API."""
    db = SessionLocal()
    req = EnergyPredictionRequest(station_id="MAITRI", horizon_hours=24)
    res = predict_energy(req, db)
    assert res.station_id == "MAITRI"
    assert res.horizon_hours == 24
    assert res.predicted_mean_load_kw > 0.0
    assert len(res.hourly_forecast) == 24
    db.close()

    # API test (Viewer access allowed)
    viewer_token = _login("viewer", "Viewer@123")
    resp = client.post(
        "/api/intelligence/energy/predict",
        json={"station_id": "MAITRI", "horizon_hours": 48},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["predicted_mean_load_kw"] > 0.0


def test_predict_fuel_service_and_api():
    """Verify predict_fuel interface via service and REST API."""
    db = SessionLocal()
    req = FuelPredictionRequest(station_id="MAITRI", horizon_days=30, generator_operational_mode="nominal")
    res = predict_fuel(req, db)
    assert res.station_id == "MAITRI"
    assert res.current_fuel_liters > 0.0
    assert res.days_of_autonomy > 0.0
    assert res.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    db.close()

    # API test
    viewer_token = _login("viewer", "Viewer@123")
    resp = client.post(
        "/api/intelligence/fuel/predict",
        json={"station_id": "MAITRI", "horizon_days": 60},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 200
    assert "days_of_autonomy" in resp.json()["data"]


def test_detect_anomaly_service_and_api():
    """Verify detect_anomaly interface via service and REST API."""
    db = SessionLocal()
    # Ingest an extreme outlier reading
    t_outlier = Telemetry(
        sensor_id=1,
        value=-72.0,  # Extreme polar outlier
        quality="POOR",
        source="SIMULATED",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(t_outlier)
    db.commit()

    req = AnomalyDetectionRequest(station_id="MAITRI", window_hours=24)
    res = detect_anomaly(req, db)
    assert res.station_id == "MAITRI"
    assert res.total_anomalies_detected >= 1
    assert any(a.observed_value == -72.0 for a in res.anomalies)
    db.close()

    # API test
    viewer_token = _login("viewer", "Viewer@123")
    resp = client.post(
        "/api/intelligence/anomalies/detect",
        json={"station_id": "MAITRI", "window_hours": 24},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["total_anomalies_detected"] >= 1


def test_calculate_risk_and_cascading_pathways():
    """Verify calculate_risk (USP 1) returns cascading nodes and persists RiskRecord in DB."""
    db = SessionLocal()
    req = RiskCalculationRequest(station_id="MAITRI", include_cascading=True)
    res = calculate_risk(req, db)
    assert res.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert len(res.cascading_pathways) > 0
    # Verify cascading node properties
    first_node = res.cascading_pathways[0]
    assert first_node.system != ""
    assert len(first_node.downstream_cascades) > 0

    # Verify database persistence
    saved_record = db.query(RiskRecord).filter(RiskRecord.station_id == 1).first()
    assert saved_record is not None
    assert saved_record.risk_type == res.risk_type
    assert len(saved_record.cascading_pathways) > 0
    db.close()

    # API test
    viewer_token = _login("viewer", "Viewer@123")
    resp = client.post(
        "/api/intelligence/risk/calculate",
        json={"station_id": "MAITRI", "include_cascading": True},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "cascading_pathways" in data


def test_what_if_simulation_and_role_protection():
    """Verify run_simulation (USP 2 What-If) and RBAC role protections."""
    controller_token = _login("controller", "Controller@123")
    viewer_token = _login("viewer", "Viewer@123")

    sim_payload = {
        "station_id": "MAITRI",
        "scenario_type": "blizzard_survival",
        "duration_hours": 72,
        "perturbations": {"ambient_temp_c": -58.0},
    }

    # 1. Viewer is blocked -> 403 Forbidden
    resp_viewer = client.post(
        "/api/intelligence/simulation/what-if",
        json=sim_payload,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp_viewer.status_code == 403

    # 2. Controller is allowed -> 200 OK
    resp_ctrl = client.post(
        "/api/intelligence/simulation/what-if",
        json=sim_payload,
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert resp_ctrl.status_code == 200
    data = resp_ctrl.json()["data"]
    assert "simulation_id" in data
    assert data["survivability_score"] > 0.0
    assert len(data["critical_events"]) > 0

    # 3. Check DB persistence of SimulationRecord
    db = SessionLocal()
    record = db.query(SimulationRecord).filter(SimulationRecord.station_id == 1).first()
    assert record is not None
    assert record.scenario_type == "blizzard_survival"
    assert record.executed_by == "controller"
    db.close()


def test_optimize_resupply_and_priority_matrix():
    """Verify optimize_resupply (USP 5 Resupply Priority Matrix) and persistence."""
    controller_token = _login("controller", "Controller@123")
    viewer_token = _login("viewer", "Viewer@123")

    resupply_payload = {
        "station_id": "MAITRI",
        "planning_horizon_days": 120,
        "icebreaker_window_days": 14,
    }

    # 1. Viewer is blocked -> 403 Forbidden
    resp_viewer = client.post(
        "/api/intelligence/resupply/optimize",
        json=resupply_payload,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp_viewer.status_code == 403

    # 2. Controller is allowed -> 200 OK
    resp_ctrl = client.post(
        "/api/intelligence/resupply/optimize",
        json=resupply_payload,
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert resp_ctrl.status_code == 200
    data = resp_ctrl.json()["data"]
    assert data["optimal_delivery_date"] != ""
    assert len(data["cargo_priorities"]) >= 3
    # Check top cargo item is fuel
    assert data["cargo_priorities"][0]["category"] == "FUEL"

    # 3. Check DB persistence of ResupplyPlanRecord
    db = SessionLocal()
    plan = db.query(ResupplyPlanRecord).filter(ResupplyPlanRecord.station_id == 1).first()
    assert plan is not None
    assert plan.status == "PROPOSED"
    assert len(plan.cargo_priorities) >= 3
    db.close()


def test_custom_developer3_provider_injection():
    """Verify that Developer 3 can inject a custom ML provider and backend routes to it seamlessly."""

    class MockDeveloper3MLProvider(BaseIntelligenceProvider):
        """Simulated custom ML intelligence module developed by Developer 3."""

        def predict_energy(self, context: TwinContext, request: EnergyPredictionRequest) -> EnergyPredictionResult:
            return EnergyPredictionResult(
                station_id=context.station_code,
                horizon_hours=request.horizon_hours,
                predicted_mean_load_kw=123.45,  # Distinctive custom ML output
                predicted_peak_load_kw=150.0,
                confidence=0.99,
                hourly_forecast=[],
                recommendation="Developer 3 PINN load model prediction",
                generated_at=datetime.now(timezone.utc),
            )

        def predict_fuel(self, context: TwinContext, request: FuelPredictionRequest) -> FuelPredictionResult:
            return FuelPredictionResult(
                station_id=context.station_code,
                current_fuel_liters=45000.0,
                daily_burn_rate_liters=650.0,
                days_of_autonomy=69.2,  # Distinctive custom output
                risk_level="LOW",
                confidence=0.95,
                generated_at=datetime.now(timezone.utc),
            )

        def detect_anomaly(self, context: TwinContext, request: AnomalyDetectionRequest) -> AnomalyDetectionResult:
            return AnomalyDetectionResult(
                station_id=context.station_code,
                total_anomalies_detected=0,
                anomalies=[],
                confidence=0.98,
                analyzed_readings_count=100,
                timestamp=datetime.now(timezone.utc),
            )

        def calculate_risk(self, context: TwinContext, request: RiskCalculationRequest) -> RiskAssessmentResult:
            return RiskAssessmentResult(
                risk_level="MEDIUM",
                risk_type="CAUSAL_DAG_RISK",
                reason="Developer 3 Causal Bayesian Network assessment",
                affected_systems=["Turbine_1"],
                cascading_pathways=[],
                recommended_action="Inspect turbine bearing",
                confidence=0.94,
                timestamp=datetime.now(timezone.utc),
            )

        def run_simulation(self, context: TwinContext, request: WhatIfSimulationRequest) -> WhatIfSimulationResult:
            return WhatIfSimulationResult(
                simulation_id="dev3-sim-999",
                station_id=context.station_code,
                scenario_type=request.scenario_type,
                duration_hours=request.duration_hours,
                survivability_score=0.99,
                summary="Developer 3 digital twin simulation output",
                metrics={"dev3_metric": 42},
                critical_events=[],
                contingencies=[],
                executed_at=datetime.now(timezone.utc),
            )

        def optimize_resupply(self, context: TwinContext, request: ResupplyOptimizationRequest) -> ResupplyOptimizationResult:
            return ResupplyOptimizationResult(
                station_id=context.station_code,
                optimal_delivery_date="2027-01-15",
                planning_horizon_days=90,
                cargo_priorities=[],
                total_cargo_volume_m3=88.8,
                risk_if_delayed="LOW",
                confidence=0.97,
                operational_notes="Developer 3 MILP optimizer output",
                generated_at=datetime.now(timezone.utc),
            )

    # 1. Register custom Developer 3 provider
    custom_provider = MockDeveloper3MLProvider()
    register_intelligence_provider(custom_provider)
    assert get_intelligence_provider() is custom_provider

    # 2. Invoke service function
    db = SessionLocal()
    energy_res = predict_energy(EnergyPredictionRequest(station_id="MAITRI", horizon_hours=12), db)
    # Confirm output was produced by the custom provider
    assert energy_res.predicted_mean_load_kw == 123.45
    assert energy_res.confidence == 0.99
    assert energy_res.recommendation == "Developer 3 PINN load model prediction"

    fuel_res = predict_fuel(FuelPredictionRequest(station_id="MAITRI", horizon_days=30), db)
    assert fuel_res.days_of_autonomy == 69.2

    db.close()

    # 3. Reset back to Fallback provider
    register_intelligence_provider(FallbackIntelligenceProvider())

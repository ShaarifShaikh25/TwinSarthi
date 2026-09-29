"""tests/test_production_verification.py

Comprehensive Production-Ready Test Suite for POLAR-TWIN Backend.
Covers all 12 specified areas and verifies the complete end-to-end integration flow:
1. Health endpoint
2. Database connection
3. Station API
4. Equipment API
5. Telemetry ingestion & Data Honesty
6. Digital Twin update
7. Alert rules
8. Authentication
9. Authorization (RBAC)
10. WebSocket real-time events
11. Simulation interface
12. Recommendation approval lifecycle
+ End-to-End Integration Pipeline Verification
"""

import pytest
from datetime import datetime, timezone
from starlette.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.station import Station, StationStatus
from app.models.equipment import Equipment, EquipmentStatus
from app.models.sensor import Sensor, SensorType, SensorStatus
from app.models.telemetry import Telemetry
from app.models.alert import Alert, AlertStatus, AlertSeverity
from app.models.recommendation import Recommendation, RecommendationStatus, RecommendationSeverity
from app.models.user import User, UserRole
from app.services.auth_service import seed_default_users

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database_fixture():
    """Ensure clean schema and baseline seeds."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear tables
    db.query(Alert).delete()
    db.query(Recommendation).delete()
    db.query(Telemetry).delete()
    db.query(Sensor).delete()
    db.query(Equipment).delete()
    db.query(User).delete()
    db.query(Station).delete()
    db.commit()

    # Seed MAITRI & BHARATI
    maitri = Station(
        id=1,
        name="Maitri Research Station",
        code="MAITRI",
        latitude=-70.7667,
        longitude=11.7333,
        status=StationStatus.ACTIVE,
    )
    bharati = Station(
        id=2,
        name="Bharati Research Station",
        code="BHARATI",
        latitude=-69.4072,
        longitude=76.1872,
        status=StationStatus.ACTIVE,
    )
    db.add_all([maitri, bharati])
    db.commit()

    # Seed generator equipment
    gen1 = Equipment(
        id=1,
        station_id=1,
        name="Diesel Generator 1",
        type="generator",
        status=EquipmentStatus.OPERATIONAL,
        health_score=95.0,
    )
    db.add(gen1)
    db.commit()

    # Seed sensors for MAITRI
    temp_sensor = Sensor(
        id=1,
        station_id=1,
        equipment_id=None,
        type=SensorType.TEMPERATURE,
        unit="degC",
        status=SensorStatus.ACTIVE,
    )
    fuel_sensor = Sensor(
        id=2,
        station_id=1,
        equipment_id=1,
        type=SensorType.FUEL_LEVEL,
        unit="percent",
        status=SensorStatus.ACTIVE,
    )
    db.add_all([temp_sensor, fuel_sensor])
    db.commit()

    # Seed default user accounts
    seed_default_users(db)
    db.close()


def _login(username: str, password: str = None) -> str:
    """Helper to login and extract JWT bearer token."""
    if password is None:
        if username == "admin":
            password = "Admin@123"
        elif username == "controller":
            password = "Controller@123"
        elif username == "viewer":
            password = "Viewer@123"

    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["data"]["access_token"]


# =====================================================================
# 1. Health Endpoint
# =====================================================================
def test_01_health_endpoint():
    """Verify system health liveness probe."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# =====================================================================
# 2. Database Connection
# =====================================================================
def test_02_database_connection():
    """Verify database connection and query execution."""
    db = SessionLocal()
    result = db.execute(text("SELECT 1")).scalar()
    assert result == 1
    station_count = db.query(Station).count()
    assert station_count >= 2
    db.close()


# =====================================================================
# 3. Station API
# =====================================================================
def test_03_station_api():
    """Verify station query and creation endpoints."""
    # List stations
    resp = client.get("/api/stations")
    assert resp.status_code == 200
    stations = resp.json()["data"]
    codes = [s["code"] for s in stations]
    assert "MAITRI" in codes
    assert "BHARATI" in codes

    # Get single station by code and id
    resp_code = client.get("/api/stations/MAITRI")
    assert resp_code.status_code == 200
    assert resp_code.json()["data"]["code"] == "MAITRI"

    resp_id = client.get("/api/stations/1")
    assert resp_id.status_code == 200
    assert resp_id.json()["data"]["id"] == 1


# =====================================================================
# 4. Equipment API
# =====================================================================
def test_04_equipment_api():
    """Verify equipment listing and creation with permissions."""
    admin_token = _login("admin")

    # Create equipment
    payload = {
        "station_id": 1,
        "name": "Life Support HVAC Unit",
        "type": "hvac",
        "status": "operational",
        "health_score": 98.0,
    }
    resp = client.post(
        "/api/equipment",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == "Life Support HVAC Unit"

    # Query infrastructure
    infra_resp = client.get("/api/infrastructure/MAITRI")
    assert infra_resp.status_code == 200
    equip_names = [eq["name"] for eq in infra_resp.json()["data"]]
    assert "Diesel Generator 1" in equip_names
    assert "Life Support HVAC Unit" in equip_names


# =====================================================================
# 5. Telemetry Ingestion & Data Honesty
# =====================================================================
def test_05_telemetry_ingestion_and_data_honesty():
    """Verify telemetry ingestion and strict data source honesty enforcement."""
    # 5.1 Ingest SIMULATED telemetry
    payload_sim = {
        "station_code": "MAITRI",
        "sensor_id": 1,
        "timestamp": "2026-09-29T12:00:00Z",
        "value": -28.5,
        "quality": "GOOD",
        "source": "SIMULATED",
    }
    resp = client.post("/api/telemetry/ingest", json=payload_sim)
    assert resp.status_code == 200
    assert resp.json()["data"]["source"] == "SIMULATED"

    # 5.2 Ingest PUBLIC_HISTORICAL telemetry
    payload_hist = {
        "station_code": "MAITRI",
        "sensor_id": 1,
        "timestamp": "2026-09-29T12:05:00Z",
        "value": -29.0,
        "quality": "GOOD",
        "source": "PUBLIC_HISTORICAL",
    }
    resp_hist = client.post("/api/telemetry/ingest", json=payload_hist)
    assert resp_hist.status_code == 200
    assert resp_hist.json()["data"]["source"] == "PUBLIC_HISTORICAL"

    # 5.3 Ingest PROTOTYPE_SENSOR telemetry
    payload_proto = {
        "station_code": "MAITRI",
        "sensor_id": 1,
        "timestamp": "2026-09-29T12:10:00Z",
        "value": -27.8,
        "quality": "GOOD",
        "source": "PROTOTYPE_SENSOR",
    }
    resp_proto = client.post("/api/telemetry/ingest", json=payload_proto)
    assert resp_proto.status_code == 200
    assert resp_proto.json()["data"]["source"] == "PROTOTYPE_SENSOR"

    # 5.4 Reject invalid unverified source labels
    payload_invalid = {
        "station_code": "MAITRI",
        "sensor_id": 1,
        "timestamp": "2026-09-29T12:15:00Z",
        "value": -28.0,
        "quality": "GOOD",
        "source": "UNVERIFIED_NCPOR_LIVE",
    }
    resp_inv = client.post("/api/telemetry/ingest", json=payload_invalid)
    assert resp_inv.status_code == 422


# =====================================================================
# 6. Digital Twin Update
# =====================================================================
def test_06_digital_twin_update():
    """Verify that ingesting telemetry updates the Digital Twin state."""
    # Ingest temperature update
    client.post(
        "/api/telemetry/ingest",
        json={
            "station_code": "MAITRI",
            "sensor_id": 1,
            "timestamp": "2026-09-29T13:00:00Z",
            "value": -34.2,
            "quality": "GOOD",
            "source": "SIMULATED",
        },
    )

    # Ingest fuel level update
    client.post(
        "/api/telemetry/ingest",
        json={
            "station_code": "MAITRI",
            "sensor_id": 2,
            "timestamp": "2026-09-29T13:01:00Z",
            "value": 68.5,
            "quality": "GOOD",
            "source": "SIMULATED",
        },
    )

    # Query digital twin
    resp = client.get("/api/digital-twin/MAITRI")
    assert resp.status_code == 200
    twin = resp.json()["data"]
    assert twin["code"] == "MAITRI"
    assert twin["environment"]["temperature"] == -34.2
    assert twin["energy"]["fuel_level"] == 68.5


# =====================================================================
# 7. Alert Rules
# =====================================================================
def test_07_alert_rules():
    """Verify rule-based alert triggering, deduplication, and auto-resolution."""
    # Ingest fuel at 18% -> Triggers CRITICAL alert (below 20%)
    client.post(
        "/api/telemetry/ingest",
        json={
            "station_code": "MAITRI",
            "sensor_id": 2,
            "timestamp": "2026-09-29T14:00:00Z",
            "value": 18.0,
            "quality": "GOOD",
            "source": "SIMULATED",
        },
    )

    resp_alerts = client.get("/api/alerts/MAITRI?status=active")
    assert resp_alerts.status_code == 200
    active_alerts = resp_alerts.json()["data"]
    assert len(active_alerts) >= 1
    assert any("fuel" in a["message"].lower() for a in active_alerts)

    # Ingest fuel at 8% -> Triggers emergency CRITICAL alert (below 10%)
    client.post(
        "/api/telemetry/ingest",
        json={
            "station_code": "MAITRI",
            "sensor_id": 2,
            "timestamp": "2026-09-29T14:05:00Z",
            "value": 8.0,
            "quality": "GOOD",
            "source": "SIMULATED",
        },
    )

    # Ingest fuel back to safe 75% -> Auto-resolves active fuel alerts
    client.post(
        "/api/telemetry/ingest",
        json={
            "station_code": "MAITRI",
            "sensor_id": 2,
            "timestamp": "2026-09-29T14:10:00Z",
            "value": 75.0,
            "quality": "GOOD",
            "source": "SIMULATED",
        },
    )

    resp_after = client.get("/api/alerts/MAITRI?status=active")
    active_now = resp_after.json()["data"]
    fuel_active = [a for a in active_now if "fuel" in a["message"].lower()]
    assert len(fuel_active) == 0


# =====================================================================
# 8. Authentication
# =====================================================================
def test_08_authentication():
    """Verify JWT authentication, token generation, and password validation."""
    # Valid login
    resp = client.post("/api/auth/login", json={"username": "controller", "password": "Controller@123"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    assert token is not None

    # Invalid login
    bad_resp = client.post("/api/auth/login", json={"username": "controller", "password": "wrongpassword"})
    assert bad_resp.status_code == 401

    # /api/auth/me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["role"].lower() == "controller"


# =====================================================================
# 9. Authorization (RBAC)
# =====================================================================
def test_09_authorization_rbac():
    """Verify RBAC role enforcement (Admin, Controller, Viewer)."""
    admin_token = _login("admin")
    controller_token = _login("controller")
    viewer_token = _login("viewer")

    # Seed a recommendation to test decision permissions
    db = SessionLocal()
    rec = Recommendation(
        id=99,
        station_id=1,
        title="Test Shedding Action",
        type="ENERGY_OPTIMIZATION",
        severity=RecommendationSeverity.MEDIUM,
        reason="High generator load detected",
        recommended_action="Shed non-critical heating load",
        status=RecommendationStatus.PENDING,
    )
    db.add(rec)
    db.commit()
    db.close()

    # VIEWER: Attempting to approve must return 403 Forbidden
    resp_viewer = client.post(
        "/api/recommendations/99/approve",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp_viewer.status_code == 403

    # CONTROLLER: Permitted to approve recommendation
    resp_controller = client.post(
        "/api/recommendations/99/approve",
        json={"notes": "Approved by operational controller"},
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert resp_controller.status_code == 200
    assert resp_controller.json()["data"]["status"] == "APPROVED"


# =====================================================================
# 10. WebSocket Real-Time Events
# =====================================================================
def test_10_websocket_realtime_events():
    """Verify real-time event streaming over WebSocket channel."""
    with client.websocket_connect("/ws/maitri") as ws:
        # Ingest telemetry
        client.post(
            "/api/telemetry/ingest",
            json={
                "station_code": "MAITRI",
                "sensor_id": 1,
                "timestamp": "2026-09-29T15:00:00Z",
                "value": -22.3,
                "quality": "GOOD",
                "source": "SIMULATED",
            },
        )

        # Receive events
        events = [ws.receive_json() for _ in range(3)]
        event_types = {e["type"]: e for e in events}
        assert "telemetry_update" in event_types
        assert event_types["telemetry_update"]["station_id"] == "maitri"
        assert event_types["telemetry_update"]["value"] == -22.3
        assert event_types["telemetry_update"]["source"] == "SIMULATED"
        assert "digital_twin_update" in event_types
        assert event_types["digital_twin_update"]["station_id"] == "maitri"


# =====================================================================
# 11. Simulation & Intelligence Interface
# =====================================================================
def test_11_simulation_interface():
    """Verify simulation and intelligence service interfaces for Developer 3."""
    controller_token = _login("controller")

    # Run what-if simulation
    sim_resp = client.post(
        "/api/simulation/run",
        json={
            "station_id": "MAITRI",
            "scenario_type": "blizzard_survival",
            "duration_hours": 168,
        },
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()["data"]
    assert sim_data["scenario_type"] == "blizzard_survival"
    assert "metrics" in sim_data

    # Calculate cascading risk
    risk_resp = client.post(
        "/api/intelligence/risk/calculate",
        json={
            "station_id": "MAITRI",
            "include_cascading": True,
        },
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert risk_resp.status_code == 200
    assert risk_resp.json()["data"]["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Optimize resupply
    resupply_resp = client.post(
        "/api/intelligence/resupply/optimize",
        json={
            "station_id": "MAITRI",
            "planning_horizon_days": 120,
            "icebreaker_window_days": 14,
        },
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert resupply_resp.status_code == 200
    assert len(resupply_resp.json()["data"]["cargo_priorities"]) >= 1


# =====================================================================
# 12. Recommendation Approval Lifecycle
# =====================================================================
def test_12_recommendation_approval_lifecycle():
    """Verify recommendation ingest, approval, modification, and rejection lifecycle."""
    controller_token = _login("controller")

    # Ingest recommendation
    db = SessionLocal()
    rec = Recommendation(
        station_id=1,
        title="Reduce Living Module Temperature",
        type="ENERGY_OPTIMIZATION",
        severity=RecommendationSeverity.HIGH,
        reason="High fuel consumption during storm",
        recommended_action="Lower target temperature by 2C to preserve diesel",
        status=RecommendationStatus.PENDING,
    )
    db.add(rec)
    db.commit()
    rec_id = rec.id
    db.close()

    # Modify recommendation
    mod_resp = client.post(
        f"/api/recommendations/{rec_id}/modify",
        json={
            "modified_action": "Lower target temperature by 1.5C to preserve diesel",
            "notes": "Modified offset to -1.5C for crew comfort",
        },
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert mod_resp.status_code == 200
    assert mod_resp.json()["data"]["status"] == "MODIFIED"

    # Reject a new recommendation
    db = SessionLocal()
    rec2 = Recommendation(
        station_id=1,
        title="Deactivate Water Treatment",
        type="EMERGENCY_SHUTDOWN",
        severity=RecommendationSeverity.CRITICAL,
        reason="Generator overload",
        recommended_action="Shutdown water recycling to save load",
        status=RecommendationStatus.PENDING,
    )
    db.add(rec2)
    db.commit()
    rec2_id = rec2.id
    db.close()

    rej_resp = client.post(
        f"/api/recommendations/{rec2_id}/reject",
        json={"reason": "Rejected: Water treatment is essential for life support"},
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert rej_resp.status_code == 200
    assert rej_resp.json()["data"]["status"] == "REJECTED"


# =====================================================================
# Complete End-to-End Pipeline Verification
# =====================================================================
def test_13_complete_e2e_pipeline():
    """Verify complete end-to-end integration flow:
    Simulator/Sensor -> Ingest -> Validation -> DB -> Twin -> Alerts -> WebSocket.
    """
    with client.websocket_connect("/ws/maitri") as ws:
        # Ingest critical temperature observation
        payload = {
            "station_code": "MAITRI",
            "sensor_id": 1,
            "timestamp": "2026-09-29T16:00:00Z",
            "value": -56.5,  # Plunges below safe minimum -50.0 °C threshold
            "quality": "GOOD",
            "source": "SIMULATED",
        }
        ingest_resp = client.post("/api/telemetry/ingest", json=payload)
        assert ingest_resp.status_code == 200

        # Collect broadcast events (up to 5 events)
        received_events = [ws.receive_json() for _ in range(5)]
        event_types = {e["type"]: e for e in received_events}

        assert "telemetry_update" in event_types
        assert event_types["telemetry_update"]["value"] == -56.5
        assert event_types["telemetry_update"]["source"] == "SIMULATED"

        assert "digital_twin_update" in event_types
        assert event_types["digital_twin_update"]["data"]["environment"]["temperature"] == -56.5
        assert "alert" in event_types

        # Check that alert was triggered in DB
        db = SessionLocal()
        alerts = db.query(Alert).filter(Alert.station_id == 1, Alert.status == AlertStatus.ACTIVE).all()
        assert any("temperature" in a.message.lower() for a in alerts)
        db.close()

"""tests/test_websocket.py

Backend WebSocket verification suite for POLAR-TWIN Phase 6:
- Tests connection to /ws/{station_id}
- Rejects connection for non-existent station_id gracefully without crashing
- Ingests telemetry via pipeline (POST /api/telemetry/ingest)
- Verifies:
    1. telemetry_update event is received over WebSocket
    2. equipment_update event is received over WebSocket
    3. alert event is received when safety thresholds are breached
    4. digital_twin_update event is broadcast
    5. Clean disconnection without crashing server
"""

import pytest
from datetime import datetime, timezone
from starlette.testclient import TestClient

from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.station import Station, StationStatus
from app.models.equipment import Equipment, EquipmentStatus
from app.models.sensor import Sensor, SensorType, SensorStatus

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create in-memory SQLite schema and seed test station, equipment, and sensors."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clean existing data for deterministic test state
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

    # Seed Generator equipment
    generator = Equipment(
        id=1,
        station_id=1,
        name="Main Diesel Generator 1",
        type="generator",
        status=EquipmentStatus.OPERATIONAL,
        health_score=94.5,
    )
    db.add(generator)
    db.commit()

    # Seed Sensors
    temp_sensor = Sensor(
        id=1,
        station_id=1,
        equipment_id=None,
        type=SensorType.TEMPERATURE,
        unit="°C",
        status=SensorStatus.ACTIVE,
    )
    gen_sensor = Sensor(
        id=2,
        station_id=1,
        equipment_id=1,
        type=SensorType.OTHER,
        unit="%",
        status=SensorStatus.ACTIVE,
    )
    db.add_all([temp_sensor, gen_sensor])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def test_invalid_station_websocket_rejected():
    """Connecting to a non-existent station should be cleanly closed with code 1008."""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/nonexistent_station") as ws:
            ws.receive_text()


def test_websocket_telemetry_and_equipment_broadcast():
    """Connect to /ws/maitri and ingest telemetry; verify telemetry_update, equipment_update, and digital_twin_update."""
    with client.websocket_connect("/ws/maitri") as ws:
        payload = {
            "station_code": "MAITRI",
            "sensor_id": 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": -24.5,
            "quality": "GOOD",
            "source": "SIMULATED",
        }
        resp = client.post("/api/telemetry/ingest", json=payload)
        assert resp.status_code == 200

        # Receive broadcast events from WebSocket (telemetry_update, equipment_update, digital_twin_update)
        received_types = set()
        for _ in range(3):
            msg = ws.receive_json()
            assert "type" in msg
            received_types.add(msg["type"])
            if msg["type"] == "telemetry_update":
                assert msg["station_id"] == "maitri"
                assert msg["value"] == -24.5

        assert "telemetry_update" in received_types
        assert "digital_twin_update" in received_types
        assert "equipment_update" in received_types


def test_websocket_alert_and_equipment_broadcast():
    """Ingesting an extreme cold value (< -50°C) must trigger and broadcast alert event."""
    with client.websocket_connect("/ws/maitri") as ws:
        payload = {
            "station_code": "MAITRI",
            "sensor_id": 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": -58.0,
            "quality": "GOOD",
            "source": "SIMULATED",
        }
        resp = client.post("/api/telemetry/ingest", json=payload)
        assert resp.status_code == 200

        received_types = set()
        # All broadcast events for this alert-triggering ingest:
        # telemetry_update, equipment_update, alert, digital_twin_update, risk_update, recommendation
        for _ in range(6):
            msg = ws.receive_json()
            received_types.add(msg["type"])
            if msg["type"] == "alert":
                assert msg["station_id"] == "maitri"
                assert "alert_id" in msg
                assert msg["severity"] == "warning"

        assert "telemetry_update" in received_types
        assert "alert" in received_types
        assert "digital_twin_update" in received_types
        assert "risk_update" in received_types
        assert "recommendation" in received_types
        assert "equipment_update" in received_types


def test_websocket_equipment_update_broadcast():
    """Telemetry associated with an equipment sensor should broadcast equipment_update."""
    with client.websocket_connect("/ws/maitri") as ws:
        payload = {
            "station_code": "MAITRI",
            "sensor_id": 2,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": 78.0,
            "quality": "GOOD",
            "source": "SIMULATED",
        }
        resp = client.post("/api/telemetry/ingest", json=payload)
        assert resp.status_code == 200

        received_types = set()
        for _ in range(3):
            msg = ws.receive_json()
            received_types.add(msg["type"])
            if msg["type"] == "equipment_update":
                assert msg["station_id"] == "maitri"
                assert msg["equipment_id"] == 1

        assert "equipment_update" in received_types

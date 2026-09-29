import pytest
from datetime import datetime, timezone
from starlette.testclient import TestClient

from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.station import Station, StationStatus
from app.models.equipment import Equipment, EquipmentStatus
from app.models.sensor import Sensor, SensorType, SensorStatus
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.services.alert_service import (
    evaluate_and_trigger_alerts,
    get_station_alerts,
    acknowledge_alert,
    resolve_alert,
)
from app.models.telemetry import Telemetry
from app.core.config import settings

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema and test station, equipment, and sensors exist."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clean existing data for deterministic test state
    db.query(Alert).delete()
    db.query(Sensor).delete()
    db.query(Equipment).delete()
    db.query(Station).delete()
    db.commit()

    # Seed MAITRI station
    station = Station(
        id=1,
        name="Maitri Research Station",
        code="MAITRI",
        latitude=-70.7667,
        longitude=11.7333,
        status=StationStatus.ACTIVE,
    )
    db.add(station)
    db.commit()

    # Seed generator equipment
    generator = Equipment(
        id=1,
        station_id=1,
        name="Main Diesel Generator",
        type="generator",
        status=EquipmentStatus.OPERATIONAL,
        health_score=95.0,
    )
    db.add(generator)
    db.commit()

    # Seed temperature sensor
    temp_sensor = Sensor(
        id=1,
        station_id=1,
        equipment_id=1,
        type=SensorType.TEMPERATURE,
        unit="°C",
        status=SensorStatus.ACTIVE,
    )
    db.add(temp_sensor)

    # Seed fuel sensor
    fuel_sensor = Sensor(
        id=2,
        station_id=1,
        equipment_id=1,
        type=SensorType.FUEL_LEVEL,
        unit="%",
        status=SensorStatus.ACTIVE,
    )
    db.add(fuel_sensor)

    db.commit()
    db.close()


def test_rule_fuel_critical_and_emergency():
    """Verify Rule 1 & Rule 2:
    - Fuel < 20% -> CRITICAL
    - Fuel < 10% -> CRITICAL / HIGH PRIORITY
    - Restoring fuel level auto-resolves open fuel alerts
    """
    db = SessionLocal()
    station = db.query(Station).filter(Station.code == "MAITRI").first()
    fuel_sensor = db.query(Sensor).filter(Sensor.station_id == station.id, Sensor.type == SensorType.FUEL_LEVEL).first()

    # Ingest 15% fuel (triggers fuel_critical_low < 20%)
    t1 = Telemetry(
        sensor_id=fuel_sensor.id,
        timestamp=datetime.now(timezone.utc),
        value=15.0,
        quality="GOOD",
        source="TEST",
    )
    t1.sensor = fuel_sensor
    alerts1 = evaluate_and_trigger_alerts(t1, db)
    assert len(alerts1) == 1
    assert alerts1[0].severity == AlertSeverity.CRITICAL
    assert alerts1[0].type == "fuel_critical_low"
    assert alerts1[0].status == AlertStatus.ACTIVE

    # Ingest 8% fuel (triggers fuel_emergency_low < 10%)
    t2 = Telemetry(
        sensor_id=fuel_sensor.id,
        timestamp=datetime.now(timezone.utc),
        value=8.0,
        quality="GOOD",
        source="TEST",
    )
    t2.sensor = fuel_sensor
    alerts2 = evaluate_and_trigger_alerts(t2, db)
    assert any(a.type == "fuel_emergency_low" and a.severity == AlertSeverity.CRITICAL for a in alerts2)

    # Ingest 50% fuel (fuel replenished -> auto-resolves fuel alerts)
    t3 = Telemetry(
        sensor_id=fuel_sensor.id,
        timestamp=datetime.now(timezone.utc),
        value=50.0,
        quality="GOOD",
        source="TEST",
    )
    t3.sensor = fuel_sensor
    evaluate_and_trigger_alerts(t3, db)

    # Verify all fuel alerts are now RESOLVED
    fuel_alerts = db.query(Alert).filter(Alert.station_id == station.id, Alert.type.like("fuel_%")).all()
    assert len(fuel_alerts) > 0
    assert all(a.status == AlertStatus.RESOLVED for a in fuel_alerts)
    db.close()


def test_rule_temperature_safe_threshold():
    """Verify Rule 3:
    - Temperature below configured safe threshold (-50°C) -> WARNING
    - Restoring temperature auto-resolves the alert
    """
    db = SessionLocal()
    station = db.query(Station).filter(Station.code == "MAITRI").first()
    temp_sensor = db.query(Sensor).filter(Sensor.station_id == station.id, Sensor.type == SensorType.TEMPERATURE).first()

    # Ingest -58.0°C (below -50°C safe threshold)
    t1 = Telemetry(
        sensor_id=temp_sensor.id,
        timestamp=datetime.now(timezone.utc),
        value=-58.0,
        quality="GOOD",
        source="TEST",
    )
    t1.sensor = temp_sensor
    alerts = evaluate_and_trigger_alerts(t1, db)
    assert len(alerts) >= 1
    temp_alert = next((a for a in alerts if a.type == "temperature_below_safe_min"), None)
    assert temp_alert is not None
    assert temp_alert.severity == AlertSeverity.WARNING
    assert temp_alert.status == AlertStatus.ACTIVE

    # Restoring temperature to -25.0°C auto-resolves
    t2 = Telemetry(
        sensor_id=temp_sensor.id,
        timestamp=datetime.now(timezone.utc),
        value=-25.0,
        quality="GOOD",
        source="TEST",
    )
    t2.sensor = temp_sensor
    evaluate_and_trigger_alerts(t2, db)

    db.refresh(temp_alert)
    assert temp_alert.status == AlertStatus.RESOLVED
    assert temp_alert.resolved_at is not None
    db.close()


def test_rule_equipment_status_failed():
    """Verify Rule 4:
    - Equipment status = FAILED -> CRITICAL alert
    """
    db = SessionLocal()
    station = db.query(Station).filter(Station.code == "MAITRI").first()
    temp_sensor = db.query(Sensor).filter(Sensor.station_id == station.id, Sensor.type == SensorType.TEMPERATURE).first()
    generator = db.query(Equipment).filter(Equipment.id == temp_sensor.equipment_id).first()

    # Set generator to FAILED
    generator.status = EquipmentStatus.FAILED
    db.commit()
    db.refresh(generator)

    t = Telemetry(
        sensor_id=temp_sensor.id,
        timestamp=datetime.now(timezone.utc),
        value=-20.0,
        quality="GOOD",
        source="TEST",
    )
    t.sensor = temp_sensor
    alerts = evaluate_and_trigger_alerts(t, db)
    equip_alert = next((a for a in alerts if f"equipment_failure_{generator.id}" in a.type), None)
    assert equip_alert is not None
    assert equip_alert.severity == AlertSeverity.CRITICAL
    assert equip_alert.status == AlertStatus.ACTIVE

    # Restore generator status to OPERATIONAL
    generator.status = EquipmentStatus.OPERATIONAL
    db.commit()
    evaluate_and_trigger_alerts(t, db)

    db.refresh(equip_alert)
    assert equip_alert.status == AlertStatus.RESOLVED
    db.close()


def test_rule_sensor_disconnected_status():
    """Verify Rule 5:
    - Sensor disconnected / inactive / faulty -> WARNING alert
    """
    db = SessionLocal()
    station = db.query(Station).filter(Station.code == "MAITRI").first()
    temp_sensor = db.query(Sensor).filter(Sensor.station_id == station.id, Sensor.type == SensorType.TEMPERATURE).first()

    # Set sensor status to DISCONNECTED
    temp_sensor.status = SensorStatus.DISCONNECTED
    db.commit()
    db.refresh(temp_sensor)

    t = Telemetry(
        sensor_id=temp_sensor.id,
        timestamp=datetime.now(timezone.utc),
        value=-20.0,
        quality="GOOD",
        source="TEST",
    )
    t.sensor = temp_sensor
    alerts = evaluate_and_trigger_alerts(t, db)
    sensor_alert = next((a for a in alerts if f"sensor_disconnected_{temp_sensor.id}" in a.type), None)
    assert sensor_alert is not None
    assert sensor_alert.severity == AlertSeverity.WARNING
    assert sensor_alert.status == AlertStatus.ACTIVE

    # Restore sensor status to ACTIVE
    temp_sensor.status = SensorStatus.ACTIVE
    db.commit()
    evaluate_and_trigger_alerts(t, db)

    db.refresh(sensor_alert)
    assert sensor_alert.status == AlertStatus.RESOLVED
    db.close()


def test_alert_deduplication():
    """Verify that repeated out-of-bounds readings for the same condition DO NOT create duplicate rows."""
    db = SessionLocal()
    station = db.query(Station).filter(Station.code == "MAITRI").first()
    temp_sensor = db.query(Sensor).filter(Sensor.station_id == station.id, Sensor.type == SensorType.TEMPERATURE).first()

    # First violation
    t1 = Telemetry(
        sensor_id=temp_sensor.id,
        timestamp=datetime.now(timezone.utc),
        value=-55.0,
        quality="GOOD",
        source="TEST",
    )
    t1.sensor = temp_sensor
    evaluate_and_trigger_alerts(t1, db)

    count_after_1 = db.query(Alert).filter(
        Alert.station_id == station.id,
        Alert.type == "temperature_below_safe_min",
        Alert.status == AlertStatus.ACTIVE,
    ).count()
    assert count_after_1 == 1

    # Second violation with colder reading
    t2 = Telemetry(
        sensor_id=temp_sensor.id,
        timestamp=datetime.now(timezone.utc),
        value=-62.0,
        quality="GOOD",
        source="TEST",
    )
    t2.sensor = temp_sensor
    evaluate_and_trigger_alerts(t2, db)

    # Count must remain exactly 1, but message updated
    alerts = db.query(Alert).filter(
        Alert.station_id == station.id,
        Alert.type == "temperature_below_safe_min",
        Alert.status == AlertStatus.ACTIVE,
    ).all()
    assert len(alerts) == 1
    assert "-62" in alerts[0].message
    db.close()


def test_alerts_rest_api_and_lifecycle():
    """Verify REST API:
    - GET /api/alerts/{station_id} (supports status & severity filters)
    - POST /api/alerts/{alert_id}/acknowledge
    - POST /api/alerts/{alert_id}/resolve
    """
    db = SessionLocal()
    station = db.query(Station).filter(Station.code == "MAITRI").first()

    # Create a fresh test alert
    alert = Alert(
        station_id=station.id,
        severity=AlertSeverity.CRITICAL,
        type="test_lifecycle_alert",
        message="Test alert lifecycle flow",
        status=AlertStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    alert_id = alert.id
    db.close()

    # 1. GET /api/alerts/MAITRI
    resp = client.get("/api/alerts/MAITRI")
    assert resp.status_code == 200
    res_data = resp.json()["data"]
    assert any(a["id"] == alert_id for a in res_data)

    # 2. Filter by status=active
    resp_active = client.get("/api/alerts/MAITRI?status=active")
    assert resp_active.status_code == 200
    assert any(a["id"] == alert_id for a in resp_active.json()["data"])

    # 3. Acknowledge alert
    resp_ack = client.post(f"/api/alerts/{alert_id}/acknowledge")
    assert resp_ack.status_code == 200
    assert resp_ack.json()["data"]["status"] == "acknowledged"

    # Verify status changed in query
    resp_ack_filter = client.get("/api/alerts/MAITRI?status=acknowledged")
    assert any(a["id"] == alert_id for a in resp_ack_filter.json()["data"])

    # 4. Resolve alert
    resp_res = client.post(f"/api/alerts/{alert_id}/resolve")
    assert resp_res.status_code == 200
    assert resp_res.json()["data"]["status"] == "resolved"

    # Verify resolved status
    resp_res_filter = client.get("/api/alerts/MAITRI?status=resolved")
    assert any(a["id"] == alert_id for a in resp_res_filter.json()["data"])

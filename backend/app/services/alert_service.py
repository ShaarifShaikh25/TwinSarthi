"""services/alert_service.py

POLAR-TWIN Rule-Based Alert Engine (Phase 7):
- Evaluates incoming telemetry and system state against centralized configurable thresholds.
- Rules implemented:
    1. Fuel < 20% -> CRITICAL
    2. Fuel < 10% -> CRITICAL / HIGH PRIORITY
    3. Temperature below configured safe threshold -> WARNING
    4. Equipment status = FAILED -> CRITICAL
    5. Sensor disconnected (status != ACTIVE) -> WARNING
    6. Extreme environmental conditions (e.g. blizzard wind > threshold) -> CRITICAL
    7. Generator load > threshold -> WARNING
- State management:
    - Statuses: ACTIVE, ACKNOWLEDGED, RESOLVED
    - Deduplication: Avoids creating duplicate alerts for the same ongoing condition
      on the same station/equipment/sensor if an ACTIVE or ACKNOWLEDGED alert already exists.
    - Updates ongoing alert timestamp/value if condition persists.
    - Auto-resolves alerts when readings return to safe operational parameters.
- Dispatches real-time WebSocket events on alert creation, update, and resolution.
- Clean interfaces prepared for Developer 3 (ML / anomaly detection).
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.telemetry import Telemetry
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.sensor import Sensor, SensorStatus
from app.models.equipment import Equipment, EquipmentStatus
from app.models.station import Station
from app.websockets.manager import ws_manager

logger = logging.getLogger(__name__)


def _safe_ws_broadcast(coro):
    """Safely fire an async broadcast coroutine from synchronous or async context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)
    except Exception as exc:
        logger.error("Failed to schedule WebSocket alert broadcast: %s", exc)


def _broadcast_alert_event(station_code: str, alert: Alert, action: str = "created"):
    """Format and broadcast real-time WebSocket alert event."""
    alert_event = {
        "type": "alert",
        "action": action,
        "station_id": station_code.lower(),
        "alert_id": alert.id,
        "severity": alert.severity.value if hasattr(alert.severity, "value") else str(alert.severity),
        "alert_type": alert.type,
        "message": alert.message,
        "status": alert.status.value if hasattr(alert.status, "value") else str(alert.status),
        "timestamp": alert.created_at.isoformat() if alert.created_at else datetime.now(timezone.utc).isoformat(),
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
    }
    _safe_ws_broadcast(ws_manager.broadcast_to_station(station_code.lower(), alert_event))


def evaluate_and_trigger_alerts(telemetry: Telemetry, db: Session) -> List[Alert]:
    """Core rule evaluation engine triggered whenever new telemetry is received.
    Deduplicates ongoing alerts and creates/updates alerts according to defined rules.
    """
    triggered: List[Alert] = []
    sensor: Optional[Sensor] = telemetry.sensor
    if not sensor:
        return triggered

    station: Optional[Station] = sensor.station
    if not station:
        station = db.query(Station).filter(Station.id == sensor.station_id).first()
    station_code = station.code.upper() if station else f"STATION-{sensor.station_id}"

    sensor_type = (sensor.type.value if hasattr(sensor.type, "value") else str(sensor.type or "")).lower()
    sensor_name = getattr(sensor, "name", None) or sensor_type
    station_id = sensor.station_id
    val = telemetry.value
    now = datetime.now(timezone.utc)

    # -------------------------------------------------------------
    # Rule 1 & 2: Fuel level threshold rules (Fuel < 20% -> CRITICAL, Fuel < 10% -> CRITICAL/HIGH PRIORITY)
    # -------------------------------------------------------------
    if sensor_type in ("fuel_level", "fuel"):
        if val < settings.ALERT_FUEL_EMERGENCY_THRESHOLD:
            # Emergency fuel level < 10%
            _record_alert(
                db=db,
                station_id=station_id,
                station_code=station_code,
                alert_type="fuel_emergency_low",
                severity=AlertSeverity.CRITICAL,
                message=f"EMERGENCY: Fuel reserve critically depleted at {val}% (< {settings.ALERT_FUEL_EMERGENCY_THRESHOLD}%) on {sensor_name}",
                triggered_list=triggered,
                now=now,
            )
        elif val < settings.ALERT_FUEL_CRITICAL_THRESHOLD:
            # Critical fuel level < 20%
            _record_alert(
                db=db,
                station_id=station_id,
                station_code=station_code,
                alert_type="fuel_critical_low",
                severity=AlertSeverity.CRITICAL,
                message=f"CRITICAL: Fuel reserve low at {val}% (< {settings.ALERT_FUEL_CRITICAL_THRESHOLD}%) on {sensor_name}",
                triggered_list=triggered,
                now=now,
            )
        else:
            # Resolve existing fuel alerts if level is restored
            _auto_resolve_alert(db, station_id, station_code, ["fuel_emergency_low", "fuel_critical_low"], now)

    # -------------------------------------------------------------
    # Rule 3: Temperature below configured safe threshold -> WARNING
    # -------------------------------------------------------------
    if sensor_type == "temperature":
        if val < settings.ALERT_TEMP_SAFE_MIN_THRESHOLD:
            _record_alert(
                db=db,
                station_id=station_id,
                station_code=station_code,
                alert_type="temperature_below_safe_min",
                severity=AlertSeverity.WARNING,
                message=f"WARNING: Temperature dropped to {val}°C (below safe threshold {settings.ALERT_TEMP_SAFE_MIN_THRESHOLD}°C) on {sensor_name}",
                triggered_list=triggered,
                now=now,
            )
        else:
            _auto_resolve_alert(db, station_id, station_code, ["temperature_below_safe_min"], now)

    # -------------------------------------------------------------
    # Rule 4: Equipment status = FAILED -> CRITICAL
    # -------------------------------------------------------------
    equipment: Optional[Equipment] = getattr(sensor, "equipment", None)
    if not equipment and sensor.equipment_id:
        equipment = db.query(Equipment).filter(Equipment.id == sensor.equipment_id).first()

    if equipment:
        equip_status_val = (
            equipment.status.value if hasattr(equipment.status, "value") else str(equipment.status or "")
        ).lower()
        if equip_status_val == EquipmentStatus.FAILED.value.lower():
            _record_alert(
                db=db,
                station_id=station_id,
                station_code=station_code,
                alert_type=f"equipment_failure_{equipment.id}",
                severity=AlertSeverity.CRITICAL,
                message=f"CRITICAL: Equipment '{equipment.name}' is in FAILED state (Health Score: {equipment.health_score})",
                triggered_list=triggered,
                now=now,
            )
        else:
            _auto_resolve_alert(db, station_id, station_code, [f"equipment_failure_{equipment.id}"], now)

    # -------------------------------------------------------------
    # Rule 5: Sensor disconnected / non-active status -> WARNING
    # -------------------------------------------------------------
    sensor_status_val = (
        sensor.status.value if hasattr(sensor.status, "value") else str(sensor.status or "")
    ).lower()
    if sensor_status_val in ("inactive", "faulty", "disconnected"):
        _record_alert(
            db=db,
            station_id=station_id,
            station_code=station_code,
            alert_type=f"sensor_disconnected_{sensor.id}",
            severity=AlertSeverity.WARNING,
            message=f"WARNING: Sensor '{sensor_name}' (ID: {sensor.id}) status is {sensor_status_val.upper()}",
            triggered_list=triggered,
            now=now,
        )
    else:
        _auto_resolve_alert(db, station_id, station_code, [f"sensor_disconnected_{sensor.id}"], now)

    # -------------------------------------------------------------
    # Rule 6: High wind blizzard condition -> CRITICAL
    # -------------------------------------------------------------
    if sensor_type == "wind":
        if val > settings.ALERT_WIND_MAX_THRESHOLD:
            _record_alert(
                db=db,
                station_id=station_id,
                station_code=station_code,
                alert_type="blizzard_wind_critical",
                severity=AlertSeverity.CRITICAL,
                message=f"CRITICAL: Extreme wind speed {val} m/s exceeds safety limit ({settings.ALERT_WIND_MAX_THRESHOLD} m/s) on {sensor_name}",
                triggered_list=triggered,
                now=now,
            )
        else:
            _auto_resolve_alert(db, station_id, station_code, ["blizzard_wind_critical"], now)

    # -------------------------------------------------------------
    # Rule 7: Generator load overload -> WARNING
    # -------------------------------------------------------------
    if sensor_type in ("generator_load", "power", "load"):
        if val > settings.ALERT_GENERATOR_LOAD_MAX_THRESHOLD:
            _record_alert(
                db=db,
                station_id=station_id,
                station_code=station_code,
                alert_type="generator_overload_warning",
                severity=AlertSeverity.WARNING,
                message=f"WARNING: Generator load {val}% exceeds safe operational limit ({settings.ALERT_GENERATOR_LOAD_MAX_THRESHOLD}%) on {sensor_name}",
                triggered_list=triggered,
                now=now,
            )
        else:
            _auto_resolve_alert(db, station_id, station_code, ["generator_overload_warning"], now)

    return triggered


def _record_alert(
    db: Session,
    station_id: int,
    station_code: str,
    alert_type: str,
    severity: AlertSeverity,
    message: str,
    triggered_list: List[Alert],
    now: datetime,
) -> Alert:
    """Record an alert ensuring deduplication:
    If an ACTIVE or ACKNOWLEDGED alert of this alert_type already exists on this station,
    update its timestamp and message without inserting a duplicate.
    Otherwise, create a new ACTIVE Alert and broadcast via WebSocket.
    """
    existing_alert: Optional[Alert] = (
        db.query(Alert)
        .filter(
            Alert.station_id == station_id,
            Alert.type == alert_type,
            Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]),
        )
        .first()
    )

    if existing_alert:
        # Deduplication: condition is ongoing. Update message and timestamp
        existing_alert.message = message
        existing_alert.updated_at = now
        existing_alert.severity = severity
        db.commit()
        db.refresh(existing_alert)
        triggered_list.append(existing_alert)
        logger.debug("Deduplicated ongoing alert ID %d (%s)", existing_alert.id, alert_type)
        return existing_alert

    # New Alert
    alert = Alert(
        station_id=station_id,
        severity=severity,
        type=alert_type,
        message=message,
        status=AlertStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    triggered_list.append(alert)
    logger.info("Created new %s alert ID %d for station %s", severity.value, alert.id, station_code)

    # Broadcast new alert over WebSocket
    _broadcast_alert_event(station_code, alert, action="created")
    return alert


def _auto_resolve_alert(
    db: Session,
    station_id: int,
    station_code: str,
    alert_types: List[str],
    now: datetime,
) -> None:
    """Auto-resolve open alerts when readings return to safe operational parameters."""
    open_alerts: List[Alert] = (
        db.query(Alert)
        .filter(
            Alert.station_id == station_id,
            Alert.type.in_(alert_types),
            Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]),
        )
        .all()
    )
    for alert in open_alerts:
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = now
        alert.updated_at = now
        db.commit()
        db.refresh(alert)
        logger.info("Auto-resolved alert ID %d (%s) for station %s", alert.id, alert.type, station_code)
        _broadcast_alert_event(station_code, alert, action="resolved")


# ---------------------------------------------------------------------------
# Management and Lifecycle Services (Acknowledgement / Resolution / Query)
# ---------------------------------------------------------------------------

def get_station_alerts(
    station_id: int,
    status_filter: Optional[str],
    severity_filter: Optional[str],
    db: Session,
) -> List[Alert]:
    """Retrieve alerts for a station with optional status and severity filtering."""
    query = db.query(Alert).filter(Alert.station_id == station_id)
    if status_filter:
        norm_status = status_filter.strip().lower()
        query = query.filter(Alert.status == norm_status)
    if severity_filter:
        norm_sev = severity_filter.strip().lower()
        query = query.filter(Alert.severity == norm_sev)
    return query.order_by(Alert.created_at.desc()).all()


def acknowledge_alert(alert_id: int, db: Session) -> Optional[Alert]:
    """Transition an active alert to ACKNOWLEDGED state and broadcast WebSocket event."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None

    now = datetime.now(timezone.utc)
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.updated_at = now
    db.commit()
    db.refresh(alert)

    station_code = alert.station.code if alert.station else f"STATION-{alert.station_id}"
    _broadcast_alert_event(station_code, alert, action="acknowledged")
    return alert


def resolve_alert(alert_id: int, db: Session) -> Optional[Alert]:
    """Transition an alert to RESOLVED state and broadcast WebSocket event."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None

    now = datetime.now(timezone.utc)
    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = now
    alert.updated_at = now
    db.commit()
    db.refresh(alert)

    station_code = alert.station.code if alert.station else f"STATION-{alert.station_id}"
    _broadcast_alert_event(station_code, alert, action="resolved")
    return alert

"""services/telemetry_service.py

Handles telemetry ingestion (both MQTT and internal API) and triggers downstream actions:
- Validation
- Database persistence
- Digital Twin update
- Alert evaluation
- WebSocket event broadcasts:
    - telemetry_update
    - equipment_update
    - alert
    - risk_update
    - recommendation
    - digital_twin_update
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.telemetry import Telemetry
from app.models.station import Station
from app.models.sensor import Sensor
from app.models.equipment import Equipment
from app.models.alert import Alert, AlertStatus
from app.services.digital_twin_service import update_station_twin, get_station_twin
from app.services.alert_service import evaluate_and_trigger_alerts
from app.websockets.manager import ws_manager

logger = logging.getLogger(__name__)


def _validate_payload(payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Validate incoming telemetry payload."""
    required = {"station_code", "sensor_id", "timestamp", "value", "quality"}
    missing = required - payload.keys()
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing fields: {', '.join(missing)}",
        )

    # Validate timestamp
    try:
        ts_val = payload["timestamp"]
        if isinstance(ts_val, str):
            ts = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
        elif isinstance(ts_val, datetime):
            ts = ts_val
        else:
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid timestamp",
        )

    # Validate quality enum
    quality = str(payload["quality"]).upper()
    if quality not in {"GOOD", "BAD", "UNCERTAIN", "UNKNOWN"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid quality",
        )

    # Validate station existence
    station_code = str(payload["station_code"]).upper()
    station = db.query(Station).filter(Station.code == station_code).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Station '{station_code}' not found",
        )

    # Validate sensor existence and belonging to station
    sensor = db.query(Sensor).filter(Sensor.id == int(payload["sensor_id"])).first()
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor ID {payload['sensor_id']} not found",
        )
    if sensor.station_id != station.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor ID {sensor.id} does not belong to station {station.code}",
        )

    # Validate data source honesty (SIMULATED, PUBLIC_HISTORICAL, PROTOTYPE_SENSOR)
    source = str(payload.get("source", "SIMULATED")).upper()
    valid_sources = {"SIMULATED", "PUBLIC_HISTORICAL", "PROTOTYPE_SENSOR"}
    if source not in valid_sources:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid telemetry source '{source}'. Must be one of: {', '.join(sorted(valid_sources))}. Never label simulated data as real NCPOR telemetry.",
        )

    return {
        **payload,
        "station_code": station_code,
        "quality": quality,
        "timestamp": ts,
        "source": source,
        "station": station,
        "sensor": sensor,
    }


def _safe_ws_broadcast(coro):
    """Safely fire an async broadcast coroutine from synchronous or async context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        # If no loop in current thread, run in a temporary loop
        asyncio.run(coro)
    except Exception as exc:
        logger.error("Failed to schedule WebSocket broadcast: %s", exc)


def ingest_telemetry(payload: Dict[str, Any], db: Session) -> Telemetry:
    """Core telemetry processing pipeline:
    1. Validation
    2. PostgreSQL persistence
    3. Digital Twin state update
    4. Alert evaluation
    5. Real-time WebSocket event broadcasting
    """
    # 1. Validation
    validated = _validate_payload(payload, db)
    sensor: Sensor = validated["sensor"]
    station: Station = validated["station"]
    station_code = station.code.lower()

    # 2. Persist telemetry row
    telemetry = Telemetry(
        source=validated.get("source", "SIMULATED"),
        timestamp=validated["timestamp"],
        value=float(validated["value"]),
        quality=validated["quality"],
        sensor_id=sensor.id,
    )
    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)

    # 3. Update Digital Twin
    try:
        update_station_twin(telemetry, db)
    except Exception as exc:
        logger.error("Digital twin update failed: %s", exc, exc_info=True)

    # 4. Evaluate alerts
    new_alerts: List[Alert] = []
    try:
        new_alerts = evaluate_and_trigger_alerts(telemetry, db)
    except Exception as exc:
        logger.error("Alert evaluation failed: %s", exc, exc_info=True)

    # 5. Broadcast WebSocket events
    sensor_display_name = getattr(sensor, "name", None) or (sensor.type.value if hasattr(sensor.type, "value") else str(sensor.type))
    # Event 1: telemetry_update
    telemetry_event = {
        "type": "telemetry_update",
        "station_id": station_code,
        "sensor": sensor_display_name,
        "sensor_id": sensor.id,
        "sensor_type": sensor.type.value if hasattr(sensor.type, "value") else str(sensor.type),
        "value": telemetry.value,
        "timestamp": telemetry.timestamp.isoformat(),
        "quality": telemetry.quality,
        "source": telemetry.source,
    }
    _safe_ws_broadcast(ws_manager.broadcast_to_station(station_code, telemetry_event))

    # Event 2: equipment_update (if this sensor is attached to equipment or affects equipment health)
    twin = get_station_twin(station.id)
    if twin and twin.equipment and twin.equipment.get("equipment_id"):
        equipment_event = {
            "type": "equipment_update",
            "station_id": station_code,
            "equipment_id": twin.equipment.get("equipment_id"),
            "equipment_name": twin.equipment.get("name"),
            "status": twin.equipment.get("status"),
            "health_score": twin.equipment.get("health_score"),
            "last_telemetry": twin.equipment.get("last_telemetry"),
            "timestamp": telemetry.timestamp.isoformat(),
        }
        _safe_ws_broadcast(ws_manager.broadcast_to_station(station_code, equipment_event))

    # Event 3: alert is broadcast directly by alert_service (evaluate_and_trigger_alerts)
    # to avoid duplicate notifications and ensure consistent action payloads.

    # Event 4: digital_twin_update (complete unified state update)
    if twin:
        twin_event = {
            "type": "digital_twin_update",
            "station_id": station_code,
            "timestamp": twin.last_updated.isoformat() if twin.last_updated else datetime.now(timezone.utc).isoformat(),
            "data": {
                "status": twin.status,
                "environment": twin.environment,
                "energy": twin.energy,
                "equipment": twin.equipment,
                "logistics": twin.logistics,
            },
        }
        _safe_ws_broadcast(ws_manager.broadcast_to_station(station_code, twin_event))

    # Event 5 & 6: risk_update & recommendation (deterministic thresholds for operational awareness)
    if new_alerts:
        risk_event = {
            "type": "risk_update",
            "station_id": station_code,
            "risk_level": "HIGH" if any("critical" in str(a.severity).lower() for a in new_alerts) else "MEDIUM",
            "active_alerts_count": len(new_alerts),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _safe_ws_broadcast(ws_manager.broadcast_to_station(station_code, risk_event))

        rec_event = {
            "type": "recommendation",
            "station_id": station_code,
            "recommendations": [
                f"Inspect {sensor_display_name} immediately due to abnormal value ({telemetry.value})"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _safe_ws_broadcast(ws_manager.broadcast_to_station(station_code, rec_event))

    return telemetry

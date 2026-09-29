"""app/services/intelligence/context.py

TwinContext Aggregator:
Assembles operational Digital Twin snapshots, historical telemetry,
equipment health, and station states into a unified TwinContext object
for consumption by Developer 3 AI and Risk intelligence models.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.station import Station
from app.models.equipment import Equipment
from app.models.telemetry import Telemetry
from app.models.sensor import Sensor
from app.models.alert import Alert, AlertStatus
from app.digital_twin.station_twin import StationTwin
from app.services.digital_twin_service import get_station_twin
from app.schemas.intelligence import TwinContext


def build_twin_context(station: Station, db: Session, telemetry_limit: int = 50) -> TwinContext:
    """Build a comprehensive TwinContext snapshot for station intelligence algorithms."""
    # 1. Fetch digital twin core state
    twin: Optional[StationTwin] = get_station_twin(station.id)
    twin_data: Dict[str, Any] = twin.model_dump() if twin and hasattr(twin, "model_dump") else {}

    env_state = twin_data.get("environment", {}) if twin_data else {}
    energy_state = twin_data.get("energy", {}) if twin_data else {}
    logistics_state = twin_data.get("logistics", {}) if twin_data else {}

    # 2. Fetch equipment records
    equipment_records: List[Equipment] = (
        db.query(Equipment)
        .filter(Equipment.station_id == station.id)
        .all()
    )
    equip_state: List[Dict[str, Any]] = [
        {
            "id": eq.id,
            "name": eq.name,
            "type": eq.type,
            "status": eq.status.value if hasattr(eq.status, "value") else str(eq.status),
            "health_score": eq.health_score,
            "last_maintenance": eq.last_maintenance.isoformat() if eq.last_maintenance else None,
            "next_maintenance": eq.next_maintenance.isoformat() if eq.next_maintenance else None,
        }
        for eq in equipment_records
    ]

    # 3. Fetch recent telemetry records
    sensors = db.query(Sensor).filter(Sensor.station_id == station.id).all()
    sensor_ids = [s.id for s in sensors]
    recent_telem_records: List[Telemetry] = []
    if sensor_ids:
        recent_telem_records = (
            db.query(Telemetry)
            .filter(Telemetry.sensor_id.in_(sensor_ids))
            .order_by(Telemetry.timestamp.desc())
            .limit(telemetry_limit)
            .all()
        )

    telemetry_list: List[Dict[str, Any]] = [
        {
            "sensor_id": t.sensor_id,
            "value": t.value,
            "quality": t.quality,
            "timestamp": t.timestamp.isoformat() if t.timestamp else None,
            "source": t.source,
        }
        for t in recent_telem_records
    ]

    # 4. Count active alerts
    active_alerts = (
        db.query(Alert)
        .filter(
            Alert.station_id == station.id,
            Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]),
        )
        .count()
    )

    return TwinContext(
        station_id=station.id,
        station_code=station.code,
        latitude=station.latitude,
        longitude=station.longitude,
        digital_twin_state=twin_data,
        environment_state=env_state,
        energy_state=energy_state,
        inventory_state=logistics_state,
        equipment_state=equip_state,
        recent_telemetry=telemetry_list,
        active_alerts_count=active_alerts,
    )

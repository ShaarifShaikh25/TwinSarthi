"""services/digital_twin_service.py

This service contains deterministic logic to maintain the *Digital Twin* state
for each station. It is deliberately lightweight and **does not** depend on any
ML models. The service is invoked from ``services.telemetry_service`` whenever
new telemetry is persisted.

The twin data is stored in a simple in‑memory cache (``station_twins`` dict).
In a production deployment you would persist the state to a dedicated table or
Redis, but for the current scope keeping it in memory satisfies the
*separate raw telemetry vs twin state* requirement.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.models.telemetry import Telemetry
from app.models.station import Station
from app.models.equipment import Equipment
from app.models.sensor import Sensor
from app.models.alert import Alert
from app.digital_twin.station_twin import StationTwin, AlertInfo
from app.digital_twin.environment_twin import EnvironmentTwin
from app.digital_twin.energy_twin import EnergyTwin
from app.digital_twin.equipment_twin import EquipmentTwin
from app.digital_twin.logistics_twin import LogisticsTwin

logger = logging.getLogger(__name__)

# In‑memory cache keyed by station_id
station_twins: Dict[int, StationTwin] = {}

# ------------------------------------------------------------------
# Helper deterministic calculations
# ------------------------------------------------------------------
def _calc_fuel_percentage(fuel_level: Optional[float], max_capacity: Optional[float]) -> Optional[float]:
    if fuel_level is None or max_capacity in (None, 0):
        return None
    return round((fuel_level / max_capacity) * 100, 2)

def _calc_estimated_fuel_hours(fuel_level: Optional[float], consumption_rate: Optional[float]) -> Optional[float]:
    if fuel_level is None or consumption_rate in (None, 0):
        return None
    return round(fuel_level / consumption_rate, 2)

def _calc_estimated_days_remaining(inventory: Optional[float], consumption_rate: Optional[float]) -> Optional[float]:
    if inventory is None or consumption_rate in (None, 0):
        return None
    return round(inventory / consumption_rate, 2)

# ------------------------------------------------------------------
# Core update entry point – called from telemetry ingestion
# ------------------------------------------------------------------
def update_station_twin(telemetry: Telemetry, db_session) -> None:
    """Update the in‑memory twin for the station related to *telemetry*.

    The function extracts the affected sensor, equipment and station models,
    updates the relevant sub‑twins, recomputes derived fields and finally
    stores the refreshed ``StationTwin`` in the ``station_twins`` cache.
    """
    # Resolve relationships – these are eager‑loaded via ORM relationships
    sensor: Sensor = telemetry.sensor
    equipment: Optional[Equipment] = getattr(sensor, "equipment", None)
    station: Station = sensor.station

    existing_twin = station_twins.get(station.id)

    # ------------------------------------------------------------------
    # 1️⃣ Build sub‑twins (environment, energy, equipment, logistics)
    # ------------------------------------------------------------------
    # Environment – preserve prior state if present
    if existing_twin and existing_twin.environment:
        env = EnvironmentTwin(**existing_twin.environment)
    else:
        env = EnvironmentTwin()

    stype = (sensor.type.value if hasattr(sensor.type, "value") else str(sensor.type)).lower()

    if telemetry.quality == "GOOD":
        if stype in ["temperature", "temp"]:
            env.temperature = telemetry.value
        elif stype in ["wind", "wind_speed"]:
            env.wind = telemetry.value
        elif stype in ["pressure", "barometer"]:
            env.pressure = telemetry.value
        elif stype in ["humidity", "relative_humidity"]:
            env.humidity = telemetry.value
        elif stype in ["visibility"]:
            env.visibility = telemetry.value
    env.last_updated = datetime.utcnow()

    # Energy – preserve prior state if present
    if existing_twin and existing_twin.energy:
        energy = EnergyTwin(**existing_twin.energy)
    else:
        energy = EnergyTwin()

    if stype in ["fuel_level", "fuel"]:
        energy.fuel_level = telemetry.value
    elif stype in ["generator_load", "load"]:
        energy.generator_load = telemetry.value

    if equipment:
        if equipment.type and equipment.type.lower() == "generator":
            if stype in ["generator_load", "load", "power"]:
                energy.generator_load = telemetry.value
            elif stype in ["fuel_level", "fuel"]:
                energy.fuel_level = telemetry.value
        elif equipment.type and equipment.type.lower() == "fuel_tank":
            energy.fuel_level = telemetry.value

    # Deterministic derived fields (assume max capacity 1000 litres / 100%)
    energy.fuel_percentage = _calc_fuel_percentage(energy.fuel_level, 1000)
    energy.estimated_fuel_remaining_hours = _calc_estimated_fuel_hours(energy.fuel_level, 5)
    energy.last_updated = datetime.utcnow()

    # Equipment – snapshot of latest telemetry + maintenance info
    equip = EquipmentTwin(
        equipment_id=equipment.id if equipment else -1,
        name=equipment.name if equipment else None,
        type=equipment.type if equipment else None,
        status=equipment.status if equipment else None,
        health_score=equipment.health_score if equipment else None,
        last_telemetry={
            "sensor_id": sensor.id,
            "value": telemetry.value,
            "timestamp": telemetry.timestamp.isoformat(),
        },
        last_maintenance=equipment.last_maintenance if equipment else None,
        next_maintenance=equipment.next_maintenance if equipment else None,
    )
    equip.last_updated = datetime.utcnow()

    # Logistics – derived from inventory records (simplified)
    logistics = LogisticsTwin()
    from app.models.inventory import Inventory
    inv_rows = db_session.query(Inventory).filter(Inventory.station_id == station.id).all()
    inventory_dict: Dict[str, Any] = {}
    for row in inv_rows:
        inventory_dict[row.item_name] = {
            "quantity": row.quantity,
            "unit": row.unit,
        }
    logistics.inventory = inventory_dict
    # Example consumption rate – using a hard‑coded value for demo
    logistics.consumption_rate = 10  # units per day (placeholder)
    logistics.minimum_required = 20   # placeholder
    logistics.estimated_days_remaining = _calc_estimated_days_remaining(
        inventory=sum(item["quantity"] for item in inventory_dict.values()) if inventory_dict else None,
        consumption_rate=logistics.consumption_rate,
    )
    logistics.last_updated = datetime.utcnow()

    # Alerts – fetch active alerts for the station
    from app.models.alert import AlertStatus
    active_alerts = (
        db_session.query(Alert)
        .filter(Alert.station_id == station.id, Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]))
        .all()
    )
    alert_infos = [
        AlertInfo(
            id=a.id,
            type=a.type,
            severity=a.severity,
            message=a.message,
            status=a.status,
            created_at=a.created_at,
        )
        for a in active_alerts
    ]

    # ------------------------------------------------------------------
    # 2️⃣ Assemble the full StationTwin
    # ------------------------------------------------------------------
    station_twin = StationTwin(
        station_id=station.id,
        name=station.name,
        code=station.code,
        status=station.status,
        environment=env.dict(),
        energy=energy.dict(),
        equipment=equip.dict(),
        logistics=logistics.dict(),
        alerts=alert_infos,
        last_updated=datetime.utcnow(),
        data_source="telemetry_service",
    )

    # Store / replace in cache
    station_twins[station.id] = station_twin
    logger.debug("Digital Twin updated for station %s", station.code)

def get_station_twin(station_id: int) -> Optional[StationTwin]:
    """Retrieve the current twin for a station if it exists."""
    return station_twins.get(station_id)

"""app/api/routes/stations.py

REST API routes for Station, Equipment, Infrastructure, Logistics, Energy, Telemetry, and Digital Twin.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user, require_role
from app.core.database import SessionLocal
from app.models.station import Station, StationStatus
from app.models.equipment import Equipment, EquipmentStatus
from app.models.sensor import Sensor, SensorType, SensorStatus
from app.models.inventory import Inventory
from app.models.telemetry import Telemetry
from app.models.user import UserRole
from app.schemas import SuccessResponse
from app.schemas.station import (
    StationCreate,
    StationOut,
    EquipmentCreate,
    EquipmentOut,
    SensorCreate,
    SensorOut,
    InventoryCreate,
    InventoryOut,
)
from app.services.digital_twin_service import get_station_twin

router = APIRouter()


def _resolve_station(station_id: str, db: Session) -> Station:
    """Helper to resolve a station by integer ID or uppercase/lowercase station code."""
    station = None
    if station_id.isdigit():
        station = db.query(Station).filter(Station.id == int(station_id)).first()
    if not station:
        station = db.query(Station).filter(Station.code.ilike(station_id)).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station '{station_id}' not found",
        )
    return station


# =====================================================================
# Station Endpoints
# =====================================================================

@router.get("/stations", response_model=SuccessResponse)
def list_stations(db: Session = Depends(get_db)):
    """List all Antarctic research stations (Maitri, Bharati, etc.)."""
    stations = db.query(Station).all()
    data = [
        {
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in stations
    ]
    return SuccessResponse(data=data)


@router.get("/stations/{station_id}", response_model=SuccessResponse)
def get_station(station_id: str, db: Session = Depends(get_db)):
    """Get single Antarctic station details by ID or code."""
    station = _resolve_station(station_id, db)
    return SuccessResponse(
        data={
            "id": station.id,
            "name": station.name,
            "code": station.code,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "status": station.status.value if hasattr(station.status, "value") else str(station.status),
            "created_at": station.created_at.isoformat() if station.created_at else None,
        }
    )


@router.post("/stations", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_station(
    payload: StationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    """Create a new station (ADMIN only)."""
    code_upper = payload.code.upper()
    existing = db.query(Station).filter(Station.code == code_upper).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Station with code '{code_upper}' already exists",
        )
    station = Station(
        name=payload.name,
        code=code_upper,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=StationStatus(payload.status.lower()) if payload.status.lower() in [s.value for s in StationStatus] else StationStatus.ACTIVE,
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    return SuccessResponse(
        data={
            "id": station.id,
            "name": station.name,
            "code": station.code,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "status": station.status.value if hasattr(station.status, "value") else str(station.status),
            "created_at": station.created_at.isoformat() if station.created_at else None,
        }
    )


# =====================================================================
# Equipment & Infrastructure Endpoints
# =====================================================================

@router.get("/infrastructure/{station_id}", response_model=SuccessResponse)
def get_station_infrastructure(station_id: str, db: Session = Depends(get_db)):
    """List equipment / infrastructure for a specific station."""
    station = _resolve_station(station_id, db)
    equipment_list = db.query(Equipment).filter(Equipment.station_id == station.id).all()
    data = [
        {
            "id": eq.id,
            "station_id": eq.station_id,
            "name": eq.name,
            "type": eq.type,
            "status": eq.status.value if hasattr(eq.status, "value") else str(eq.status),
            "health_score": eq.health_score,
            "last_maintenance": eq.last_maintenance.isoformat() if eq.last_maintenance else None,
            "next_maintenance": eq.next_maintenance.isoformat() if eq.next_maintenance else None,
        }
        for eq in equipment_list
    ]
    return SuccessResponse(data=data)


@router.post("/equipment", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_equipment(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role([UserRole.ADMIN, UserRole.CONTROLLER])),
):
    """Add equipment to a station (ADMIN/CONTROLLER only)."""
    station = db.query(Station).filter(Station.id == payload.station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with ID {payload.station_id} not found",
        )
    equip_status = EquipmentStatus.OPERATIONAL
    if payload.status.lower() in [s.value for s in EquipmentStatus]:
        equip_status = EquipmentStatus(payload.status.lower())

    eq = Equipment(
        station_id=station.id,
        name=payload.name,
        type=payload.type,
        status=equip_status,
        health_score=payload.health_score if payload.health_score is not None else 100.0,
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return SuccessResponse(
        data={
            "id": eq.id,
            "station_id": eq.station_id,
            "name": eq.name,
            "type": eq.type,
            "status": eq.status.value if hasattr(eq.status, "value") else str(eq.status),
            "health_score": eq.health_score,
        }
    )


# =====================================================================
# Sensors & Inventory CRUD
# =====================================================================

@router.post("/sensors", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(
    payload: SensorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role([UserRole.ADMIN, UserRole.CONTROLLER])),
):
    """Register a new telemetry sensor for a station (ADMIN/CONTROLLER only)."""
    station = db.query(Station).filter(Station.id == payload.station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with ID {payload.station_id} not found",
        )
    sensor_type = SensorType.OTHER
    if payload.type.lower() in [t.value for t in SensorType]:
        sensor_type = SensorType(payload.type.lower())

    sensor = Sensor(
        station_id=station.id,
        equipment_id=payload.equipment_id,
        type=sensor_type,
        unit=payload.unit,
        status=SensorStatus(payload.status.lower()) if payload.status.lower() in [s.value for s in SensorStatus] else SensorStatus.ACTIVE,
    )
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return SuccessResponse(
        data={
            "id": sensor.id,
            "station_id": sensor.station_id,
            "equipment_id": sensor.equipment_id,
            "type": sensor.type.value if hasattr(sensor.type, "value") else str(sensor.type),
            "unit": sensor.unit,
            "status": sensor.status.value if hasattr(sensor.status, "value") else str(sensor.status),
        }
    )


@router.post("/inventory", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(
    payload: InventoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role([UserRole.ADMIN, UserRole.CONTROLLER])),
):
    """Create or register an inventory asset for a station (ADMIN/CONTROLLER only)."""
    station = db.query(Station).filter(Station.id == payload.station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with ID {payload.station_id} not found",
        )
    inv = Inventory(
        station_id=station.id,
        item_name=payload.item_name,
        category=payload.category,
        quantity=payload.quantity,
        unit=payload.unit,
        consumption_rate=payload.consumption_rate,
        minimum_required=payload.minimum_required,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return SuccessResponse(
        data={
            "id": inv.id,
            "station_id": inv.station_id,
            "item_name": inv.item_name,
            "category": inv.category,
            "quantity": inv.quantity,
            "unit": inv.unit,
            "consumption_rate": inv.consumption_rate,
            "minimum_required": inv.minimum_required,
        }
    )


# =====================================================================
# Telemetry Query Endpoints
# =====================================================================

@router.get("/telemetry", response_model=SuccessResponse)
def get_recent_telemetry(limit: int = 50, db: Session = Depends(get_db)):
    """Fetch latest telemetry points across all sensors."""
    rows = db.query(Telemetry).order_by(Telemetry.timestamp.desc()).limit(limit).all()
    data = [
        {
            "id": r.id,
            "sensor_id": r.sensor_id,
            "value": r.value,
            "quality": r.quality,
            "source": r.source,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]
    return SuccessResponse(data=data)


@router.get("/telemetry/{station_id}", response_model=SuccessResponse)
def get_station_telemetry(station_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Fetch latest telemetry points for a specific station."""
    station = _resolve_station(station_id, db)
    rows = (
        db.query(Telemetry)
        .join(Sensor, Telemetry.sensor_id == Sensor.id)
        .filter(Sensor.station_id == station.id)
        .order_by(Telemetry.timestamp.desc())
        .limit(limit)
        .all()
    )
    data = [
        {
            "id": r.id,
            "sensor_id": r.sensor_id,
            "sensor_type": r.sensor.type.value if hasattr(r.sensor.type, "value") else str(r.sensor.type),
            "value": r.value,
            "quality": r.quality,
            "source": r.source,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]
    return SuccessResponse(data=data)


# =====================================================================
# Digital Twin, Energy & Logistics Views
# =====================================================================

@router.get("/digital-twin/{station_id}", response_model=SuccessResponse)
def get_digital_twin_state(station_id: str, db: Session = Depends(get_db)):
    """Fetch unified real-time Digital Twin state for a station."""
    station = _resolve_station(station_id, db)
    twin = get_station_twin(station.id)
    if not twin:
        # Fallback default initial twin state if no telemetry ingested yet
        twin_data = {
            "station_id": station.id,
            "name": station.name,
            "code": station.code,
            "status": station.status.value if hasattr(station.status, "value") else str(station.status),
            "environment": {"temperature": -20.0, "wind_speed": 12.0, "pressure": 985.0, "humidity": 70.0},
            "energy": {"total_load_kw": 85.0, "solar_generation_kw": 25.0, "wind_generation_kw": 20.0, "fuel_level_litres": 15000.0, "fuel_percentage": 75.0},
            "equipment": {"status": "operational", "health_score": 98.0},
            "logistics": {"fuel_days_remaining": 120.0, "food_days_remaining": 240.0, "medical_days_remaining": 180.0},
            "alerts": [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "data_source": "INITIAL_DIGITAL_TWIN",
        }
    else:
        twin_data = twin.model_dump() if hasattr(twin, "model_dump") else twin.dict()
        if "last_updated" in twin_data and isinstance(twin_data["last_updated"], datetime):
            twin_data["last_updated"] = twin_data["last_updated"].isoformat()
    return SuccessResponse(data=twin_data)


@router.get("/energy/{station_id}", response_model=SuccessResponse)
def get_station_energy_state(station_id: str, db: Session = Depends(get_db)):
    """Fetch current energy twin metrics (fuel, generators, renewable ratio)."""
    station = _resolve_station(station_id, db)
    twin = get_station_twin(station.id)
    if twin and twin.energy:
        energy_data = twin.energy
    else:
        energy_data = {
            "total_load_kw": 85.0,
            "solar_generation_kw": 25.0,
            "wind_generation_kw": 20.0,
            "dg_generation_kw": 40.0,
            "fuel_level_litres": 15000.0,
            "fuel_percentage": 75.0,
            "renewable_fraction_pct": 52.9,
            "battery_soc_pct": 88.0,
            "status": "OPTIMAL",
        }
    return SuccessResponse(data={"station_code": station.code, "energy": energy_data})


@router.get("/logistics/{station_id}", response_model=SuccessResponse)
def get_station_logistics_state(station_id: str, db: Session = Depends(get_db)):
    """Fetch current logistics & inventory status (fuel days, critical spares, medical)."""
    station = _resolve_station(station_id, db)
    items = db.query(Inventory).filter(Inventory.station_id == station.id).all()
    inventory_data = [
        {
            "id": it.id,
            "item_name": it.item_name,
            "category": it.category,
            "quantity": it.quantity,
            "unit": it.unit,
            "consumption_rate": it.consumption_rate,
            "days_remaining": round(it.quantity / it.consumption_rate, 1) if it.consumption_rate and it.consumption_rate > 0 else None,
            "minimum_required": it.minimum_required,
            "critical_shortage": (it.quantity < it.minimum_required) if it.minimum_required else False,
        }
        for it in items
    ]
    twin = get_station_twin(station.id)
    logistics_summary = twin.logistics if (twin and twin.logistics) else {
        "fuel_days_remaining": 120.0,
        "resupply_urgency": "NORMAL",
    }
    return SuccessResponse(
        data={
            "station_code": station.code,
            "summary": logistics_summary,
            "inventory": inventory_data,
        }
    )

"""app/core/init_db.py

Automatic database initialization and baseline seeder for POLAR-TWIN.
Ensures stations, users, equipment, and sensors are ready on application startup.
"""

import logging
from app.core.database import Base, engine, SessionLocal
from app.models.station import Station, StationStatus
from app.models.equipment import Equipment, EquipmentStatus
from app.models.sensor import Sensor, SensorType, SensorStatus
from app.models.inventory import Inventory
from app.services.auth_service import seed_default_users

logger = logging.getLogger(__name__)


def init_db():
    """Create all relational tables and seed baseline demonstration entities."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed stations (Maitri and Bharati)
        maitri = db.query(Station).filter(Station.code == "MAITRI").first()
        if not maitri:
            maitri = Station(
                id=1,
                name="Maitri Research Station",
                code="MAITRI",
                latitude=-70.7667,
                longitude=11.7333,
                status=StationStatus.ACTIVE,
            )
            db.add(maitri)

        bharati = db.query(Station).filter(Station.code == "BHARATI").first()
        if not bharati:
            bharati = Station(
                id=2,
                name="Bharati Research Station",
                code="BHARATI",
                latitude=-69.4072,
                longitude=76.1872,
                status=StationStatus.ACTIVE,
            )
            db.add(bharati)
        db.commit()

        # 2. Seed baseline default users (admin, controller, viewer)
        seed_default_users(db)

        # 3. Seed baseline equipment
        gen1 = db.query(Equipment).filter(Equipment.name == "Diesel Generator 1").first()
        if not gen1:
            gen1 = Equipment(
                id=1,
                station_id=1,
                name="Diesel Generator 1",
                type="generator",
                status=EquipmentStatus.OPERATIONAL,
                health_score=96.5,
            )
            db.add(gen1)
            db.commit()

        # 4. Seed baseline sensors for Maitri
        temp_s = db.query(Sensor).filter(Sensor.id == 1).first()
        if not temp_s:
            temp_s = Sensor(
                id=1,
                station_id=1,
                equipment_id=None,
                type=SensorType.TEMPERATURE,
                unit="degC",
                status=SensorStatus.ACTIVE,
            )
            db.add(temp_s)

        fuel_s = db.query(Sensor).filter(Sensor.id == 2).first()
        if not fuel_s:
            fuel_s = Sensor(
                id=2,
                station_id=1,
                equipment_id=1,
                type=SensorType.FUEL_LEVEL,
                unit="percent",
                status=SensorStatus.ACTIVE,
            )
            db.add(fuel_s)
        db.commit()

        # 5. Seed baseline inventory
        fuel_inv = db.query(Inventory).filter(Inventory.item_name == "Arctic Diesel Fuel").first()
        if not fuel_inv:
            fuel_inv = Inventory(
                station_id=1,
                item_name="Arctic Diesel Fuel",
                category="FUEL",
                quantity=14200.0,
                unit="litres",
                consumption_rate=120.0,
                minimum_required=3000.0,
            )
            db.add(fuel_inv)
            db.commit()

        logger.info("Database initialized with baseline Antarctic research stations and accounts.")
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc, exc_info=True)
        db.rollback()
    finally:
        db.close()

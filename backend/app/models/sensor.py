from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class SensorType(str, enum.Enum):
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    HUMIDITY = "humidity"
    WIND = "wind"
    FUEL_LEVEL = "fuel_level"
    POWER = "power"
    GENERATOR_LOAD = "generator_load"
    OTHER = "other"

class SensorStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAULTY = "faulty"
    DISCONNECTED = "disconnected"

class Sensor(Base):
    __tablename__ = "sensors"
    __table_args__ = (
        Index("ix_sensor_station_id", "station_id"),
        Index("ix_sensor_equipment_id", "equipment_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True)
    type = Column(Enum(SensorType), nullable=False)
    unit = Column(String, nullable=False)
    status = Column(Enum(SensorStatus), nullable=False, default=SensorStatus.ACTIVE)

    # Relationships
    station = relationship("Station", back_populates="sensors")
    equipment = relationship("Equipment", back_populates="sensors")
    telemetry = relationship("Telemetry", back_populates="sensor", cascade="all, delete-orphan")

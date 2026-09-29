from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum, ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class StationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class Station(Base):
    __tablename__ = "stations"
    __table_args__ = (Index("ix_station_code", "code", unique=True),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(Enum(StationStatus), nullable=False, default=StationStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    equipment = relationship("Equipment", back_populates="station", cascade="all, delete-orphan")
    sensors = relationship("Sensor", back_populates="station", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="station", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="station", cascade="all, delete-orphan")

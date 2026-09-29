from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class EquipmentStatus(str, enum.Enum):
    OPERATIONAL = "operational"
    FAILED = "failed"
    MAINTENANCE = "maintenance"

class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (Index("ix_equipment_station_id", "station_id"),)

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(Enum(EquipmentStatus), nullable=False, default=EquipmentStatus.OPERATIONAL)
    health_score = Column(Float, nullable=True)
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    next_maintenance = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    station = relationship("Station", back_populates="equipment")
    sensors = relationship("Sensor", back_populates="equipment", cascade="all, delete-orphan")
    maintenance = relationship("Maintenance", back_populates="equipment", cascade="all, delete-orphan")

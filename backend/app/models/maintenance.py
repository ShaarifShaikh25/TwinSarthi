from sqlalchemy import Column, Integer, DateTime, Enum, String, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Maintenance(Base):
    __tablename__ = "maintenance"
    __table_args__ = (Index("ix_maintenance_equipment_id", "equipment_id"),)

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(MaintenanceStatus), nullable=False, default=MaintenanceStatus.SCHEDULED)
    description = Column(String, nullable=True)

    equipment = relationship("Equipment", back_populates="maintenance")

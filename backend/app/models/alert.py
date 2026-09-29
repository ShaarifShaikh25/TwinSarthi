from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    OPEN = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alert_station_id", "station_id"),
        Index("ix_alert_station_status", "station_id", "status"),
        Index("ix_alert_type", "type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    station = relationship("Station", back_populates="alerts")

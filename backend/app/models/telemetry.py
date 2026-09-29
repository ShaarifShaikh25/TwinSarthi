from sqlalchemy import Column, Integer, DateTime, Float, String, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Telemetry(Base):
    __tablename__ = "telemetry"
    __table_args__ = (
        Index("ix_telemetry_sensor_id", "sensor_id"),
        Index("ix_telemetry_timestamp", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False)
    source = Column(String, nullable=False, default="SIMULATED")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    value = Column(Float, nullable=False)
    quality = Column(String, nullable=True)

    # Relationships
    sensor = relationship("Sensor", back_populates="telemetry")

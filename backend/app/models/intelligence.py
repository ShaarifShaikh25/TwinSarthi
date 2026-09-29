"""app/models/intelligence.py

Database Models for POLAR-TWIN AI, Risk, Simulation, and Resupply Optimization records.
Provides persistence layer for Developer 3 intelligence outputs:
1. Cascading Risk Assessments
2. What-If Simulation Runs
3. Resupply Optimization Plans
"""

import enum
from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskRecord(Base):
    __tablename__ = "risk_assessments"
    __table_args__ = (
        Index("ix_risk_station_id", "station_id"),
        Index("ix_risk_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    risk_level = Column(String(20), nullable=False, default=RiskLevel.MEDIUM.value)
    risk_type = Column(String(50), nullable=False)  # FUEL, THERMAL, POWER, STRUCTURAL, LOGISTICS
    reason = Column(Text, nullable=False)
    affected_systems = Column(JSON, nullable=False, default=list)
    cascading_pathways = Column(JSON, nullable=True, default=list)  # USP 1: Cascading Risk Graph
    recommended_action = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.85)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    station = relationship("Station", backref="risk_assessments")


class SimulationRecord(Base):
    __tablename__ = "simulation_records"
    __table_args__ = (
        Index("ix_sim_station_id", "station_id"),
        Index("ix_sim_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(String(50), unique=True, index=True, nullable=False)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    scenario_type = Column(String(100), nullable=False)  # USP 2: What-If Scenario
    duration_hours = Column(Integer, nullable=False, default=24)
    survivability_score = Column(Float, nullable=False, default=1.0)
    summary = Column(Text, nullable=False)
    metrics = Column(JSON, nullable=False, default=dict)
    critical_events = Column(JSON, nullable=True, default=list)
    recommended_contingencies = Column(JSON, nullable=True, default=list)
    executed_by = Column(String(50), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    station = relationship("Station", backref="simulation_records")


class ResupplyPlanRecord(Base):
    __tablename__ = "resupply_plans"
    __table_args__ = (
        Index("ix_resupply_station_id", "station_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    optimal_resupply_date = Column(String(50), nullable=False)
    planning_horizon_days = Column(Integer, nullable=False, default=90)
    cargo_priorities = Column(JSON, nullable=False, default=list)  # USP 5: Resupply Priority Matrix
    required_volume_m3 = Column(Float, nullable=False, default=0.0)
    risk_if_delayed = Column(String(50), nullable=False, default="MEDIUM")
    status = Column(String(20), nullable=False, default="PROPOSED")  # PROPOSED, APPROVED, IN_TRANSIT
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    station = relationship("Station", backref="resupply_plans")

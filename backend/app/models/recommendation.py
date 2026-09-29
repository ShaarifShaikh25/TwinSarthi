"""app/models/recommendation.py

Recommendation and Decision Audit Models for POLAR-TWIN Phase 8.
Stores AI/Risk recommendations and tracks human-in-the-loop decisions (approve, modify, reject).
"""

import enum
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class RecommendationSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    MODIFIED = "MODIFIED"
    REJECTED = "REJECTED"


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        Index("ix_recommendation_station_status", "station_id", "status"),
        Index("ix_recommendation_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False, default="general")
    severity = Column(Enum(RecommendationSeverity), nullable=False, default=RecommendationSeverity.MEDIUM)
    title = Column(String(200), nullable=False)
    reason = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.85)
    status = Column(Enum(RecommendationStatus), nullable=False, default=RecommendationStatus.PENDING)

    # Decision audit tracking
    decided_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    modified_action = Column(Text, nullable=True)
    decision_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    station = relationship("Station", backref="recommendations")
    decided_by_user = relationship("User", back_populates="decisions")
    audits = relationship("RecommendationAudit", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationAudit(Base):
    __tablename__ = "recommendation_audits"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    recommendation = relationship("Recommendation", back_populates="audits")
    user = relationship("User", back_populates="audit_logs")

"""app/models/user.py

User and Role Models for POLAR-TWIN Role-Based Access Control (RBAC).
Roles:
- ADMIN: Full access
- CONTROLLER: View, run simulations, approve/modify/reject recommendations
- VIEWER: Read-only access
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CONTROLLER = "controller"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    decisions = relationship("Recommendation", back_populates="decided_by_user")
    audit_logs = relationship("RecommendationAudit", back_populates="user")

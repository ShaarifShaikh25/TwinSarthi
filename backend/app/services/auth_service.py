"""app/services/auth_service.py

Authentication service providing user creation, credential validation,
and automatic default role seeding (Admin, Controller, Viewer).
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password

logger = logging.getLogger(__name__)


def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """Validate username and password against stored database credentials."""
    user: Optional[User] = db.query(User).filter(User.username == username.strip()).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(
    username: str,
    email: str,
    password: str,
    role: UserRole,
    db: Session,
) -> User:
    """Create a new user with encrypted password hash."""
    hashed = hash_password(password)
    user = User(
        username=username.strip(),
        email=email.strip().lower(),
        hashed_password=hashed,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created user '%s' with role '%s'", user.username, user.role.value)
    return user


def seed_default_users(db: Session) -> None:
    """Ensure baseline demonstration accounts exist for Admin, Controller, and Viewer roles."""
    defaults = [
        ("admin", "admin@polartwin.aq", "Admin@123", UserRole.ADMIN),
        ("controller", "controller@polartwin.aq", "Controller@123", UserRole.CONTROLLER),
        ("viewer", "viewer@polartwin.aq", "Viewer@123", UserRole.VIEWER),
    ]
    for username, email, pwd, role in defaults:
        existing = db.query(User).filter(User.username == username).first()
        if not existing:
            create_user(username, email, pwd, role, db)
            logger.info("Seeded default %s account: '%s'", role.value, username)

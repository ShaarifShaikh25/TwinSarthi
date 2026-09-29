"""app/api/dependencies.py

FastAPI dependency injection utilities:
- Database session provider (get_db)
- Authenticated user retrieval (get_current_user)
- Role-Based Access Control (require_role)
"""

from typing import List, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import oauth2_scheme, decode_access_token
from app.models.user import User, UserRole


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Retrieve and validate the currently authenticated user from the Bearer JWT."""
    token_data = decode_access_token(token)
    user: User = db.query(User).filter(User.username == token_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return user


def require_role(allowed_roles: List[UserRole]) -> Callable[[User], User]:
    """Dependency factory that restricts endpoint access to specified roles.
    ADMIN role has superuser privileges across all routes.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role
        # ADMIN has full access across all operations
        if user_role == UserRole.ADMIN:
            return current_user

        if user_role not in allowed_roles:
            role_val = user_role.value if hasattr(user_role, "value") else str(user_role)
            allowed_vals = [r.value if hasattr(r, "value") else str(r) for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient permissions. Role '{role_val}' is not in allowed roles: {allowed_vals}",
            )
        return current_user

    return role_checker


__all__ = ["get_db", "get_current_user", "require_role"]

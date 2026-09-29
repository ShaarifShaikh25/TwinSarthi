"""app/api/routes/auth.py

Authentication API Routes:
- POST /api/auth/login: Authenticate credentials and return JWT bearer token
- GET /api/auth/me: Return current authenticated user profile and assigned role
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.schemas import SuccessResponse
from app.services.auth_service import authenticate_user, seed_default_users

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=SuccessResponse)
def login_endpoint(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate with username and password, returning JWT access token."""
    # Ensure default accounts are present
    seed_default_users(db)

    user = authenticate_user(credentials.username, credentials.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": role_str,
        }
    )

    token_data = TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=role_str,
    )
    return SuccessResponse(
        message="Authentication successful",
        data=token_data.model_dump(),
    )


@router.get("/me", response_model=SuccessResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve profile and assigned role for the authenticated user."""
    role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    user_out = UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=role_str,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
    return SuccessResponse(data=user_out.model_dump())

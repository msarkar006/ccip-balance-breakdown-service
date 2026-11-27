"""
Auth domain router - API endpoints for authentication.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.auth_models import AppUser, UserSession
from app.auth.auth_schemas import (
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    SessionRevokeResponse,
    StepUpRequest,
    StepUpResponse,
)
from app.auth.auth_service import AuthService
from app.core.database import get_db
from app.middleware.auth import get_current_user, get_current_user_session

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    Login endpoint - authenticate user and create session.

    Args:
        request: Login request with email and password
        db: Database session

    Returns:
        Login response with JWT token and user information
    """
    service = AuthService(db)
    return service.login(request.email, request.password)


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
def logout(
    user_session: tuple[AppUser, UserSession] = Depends(get_current_user_session),
    db: Session = Depends(get_db)
) -> LogoutResponse:
    """
    Logout endpoint - revoke current session.

    Args:
        user_session: Current authenticated user and session
        db: Database session

    Returns:
        Logout response
    """
    user, session = user_session
    service = AuthService(db)
    return service.logout(session.id)


@router.delete("/sessions/{session_id}", response_model=SessionRevokeResponse, status_code=status.HTTP_200_OK)
def revoke_session(
    session_id: int,
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SessionRevokeResponse:
    """
    Revoke a specific session.

    Args:
        session_id: ID of session to revoke
        user: Current authenticated user
        db: Database session

    Returns:
        Session revoke response
    """
    service = AuthService(db)
    return service.revoke_session(session_id, user.id)


@router.post("/step-up", response_model=StepUpResponse, status_code=status.HTTP_200_OK)
def step_up(
    request: StepUpRequest,
    user_session: tuple[AppUser, UserSession] = Depends(get_current_user_session),
    db: Session = Depends(get_db)
) -> StepUpResponse:
    """
    Step-up authentication endpoint - elevate session to high-risk context.

    Args:
        request: Step-up request with password
        user_session: Current authenticated user and session
        db: Database session

    Returns:
        Step-up response with validity timestamp
    """
    user, session = user_session
    service = AuthService(db)
    return service.step_up(user, session, request.password)


@router.get("/me", response_model=CurrentUserResponse, status_code=status.HTTP_200_OK)
def get_me(
    user_session: tuple[AppUser, UserSession] = Depends(get_current_user_session),
    db: Session = Depends(get_db)
) -> CurrentUserResponse:
    """
    Get current user information.

    Args:
        user_session: Current authenticated user and session
        db: Database session

    Returns:
        Current user response with session details
    """
    user, session = user_session
    service = AuthService(db)
    return service.get_current_user_response(user, session)

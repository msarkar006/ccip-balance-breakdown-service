"""Authentication and session endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentUser, get_current_user
from app.schemas.auth_schemas import LoginRequest, LoginResponse, SessionInfo
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, response_model_by_alias=True)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    source_ip = request.client.host if request.client else "unknown"
    return AuthService(db).login(payload.username, payload.password, source_ip)


@router.post("/logout", status_code=204)
def logout(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    AuthService(db).logout(user)
    return Response(status_code=204)


@router.get("/session", response_model=SessionInfo, response_model_by_alias=True)
def session_info(user: CurrentUser = Depends(get_current_user)) -> SessionInfo:
    return SessionInfo(
        user=user.summary(),
        issued_at=user.issued_at,
        expires_at=user.expires_at,
        last_activity_at=user.last_activity_at,
    )

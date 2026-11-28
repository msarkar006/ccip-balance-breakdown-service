"""Authentication and authorization dependencies: the single `get_current_user`."""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import AuthenticationError, ForbiddenError
from app.services.auth_service import AuthService, CurrentUser

__all__ = ["CurrentUser", "get_current_user", "require_customer"]

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("missing bearer token")
    return AuthService(db).authenticate(credentials.credentials)


def require_customer(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "customer" or user.customer_id is None:
        raise ForbiddenError("customer role required")
    return user

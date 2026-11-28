"""Login (Algorithm C) and session validation (Algorithm B)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import bcrypt
import jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import AuthenticationError, RateLimitedError
from app.models import AppUser, UserSession
from app.repositories.session_repository import SessionRepository, hash_token
from app.repositories.setting_repository import SettingRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schemas import LoginResponse, UserSummary
from app.services.audit_service import AuditService
from app.services.login_rate_limiter import LoginRateLimiter, login_rate_limiter
from app.utils import to_utc

BCRYPT_COST = 12
JWT_ALGORITHM = "HS256"
DEFAULT_INACTIVITY_MINUTES = 15
DEFAULT_LIFETIME_MINUTES = 60
LOGIN_FAILURE_TEXT = "Invalid username or password"


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    username: str
    role: str
    customer_id: uuid.UUID | None
    session_id: uuid.UUID
    issued_at: datetime
    expires_at: datetime
    last_activity_at: datetime

    def summary(self) -> UserSummary:
        return UserSummary(
            id=self.id,
            username=self.username,
            role="administrator" if self.role == "administrator" else "customer",
            customer_id=self.customer_id,
        )


class InvalidCredentialsError(AuthenticationError):
    public_detail = LOGIN_FAILURE_TEXT


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_COST)).decode("ascii")


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    return hash_password("dummy-password-for-timing")


class AuthService:
    def __init__(self, db: Session, limiter: LoginRateLimiter | None = None) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.sessions = SessionRepository(db)
        self.settings = SettingRepository(db)
        self.audit = AuditService(db)
        self.limiter = limiter or login_rate_limiter

    # -- Algorithm C -----------------------------------------------------------------
    def login(self, username: str, password: str, source_ip: str) -> LoginResponse:
        if self.limiter.is_limited(source_ip):
            self.audit.record_committed(
                event_type="login_failure",
                entity_type="app_user",
                severity="warning",
                detail="rate limited",
            )
            raise RateLimitedError(self.limiter.retry_after(source_ip))

        user = self.users.get_by_username(username)
        if user is None or not user.is_active:
            bcrypt.checkpw(password.encode("utf-8"), _dummy_hash().encode("ascii"))
            password_ok = False
        else:
            password_ok = bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("ascii"))
        if user is None or not user.is_active or not password_ok:
            self.limiter.record_failure(source_ip)
            self.audit.record_committed(
                event_type="login_failure",
                entity_type="app_user",
                severity="warning",
                entity_id=str(user.id) if user else None,
                actor_user_id=user.id if user else None,
                detail="invalid credentials",
            )
            raise InvalidCredentialsError("login failed")

        return self._open_session(user)

    def _open_session(self, user: AppUser) -> LoginResponse:
        now = datetime.now(UTC)
        lifetime = self.settings.get_int("session.max_lifetime_minutes", DEFAULT_LIFETIME_MINUTES)
        inactivity = self.settings.get_int("session.inactivity_timeout_minutes", DEFAULT_INACTIVITY_MINUTES)
        expires = now + timedelta(minutes=lifetime)
        token = jwt.encode(
            {
                "sub": str(user.id),
                "iat": int(now.timestamp()),
                "exp": int(expires.timestamp()),
                "jti": uuid.uuid4().hex,
            },
            get_settings().jwt_secret_key,
            algorithm=JWT_ALGORITHM,
        )
        session = self.sessions.create(user.id, hash_token(token), now, expires)
        self.users.touch_last_login(user, now)
        self.audit.record(
            event_type="login_success",
            entity_type="user_session",
            entity_id=str(session.id),
            actor_user_id=user.id,
            detail="login succeeded",
        )
        self.db.commit()
        return LoginResponse(
            access_token=token,
            issued_at=now,
            expires_at=expires,
            inactivity_timeout_minutes=inactivity,
            user=UserSummary(
                id=user.id,
                username=user.username,
                role="administrator" if user.role == "administrator" else "customer",
                customer_id=user.customer_id,
            ),
        )

    # -- Algorithm B -----------------------------------------------------------------
    def authenticate(self, token: str) -> CurrentUser:
        try:
            jwt.decode(
                token,
                get_settings().jwt_secret_key,
                algorithms=[JWT_ALGORITHM],
                options={"require": ["exp", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("invalid token") from exc

        session = self.sessions.find_by_token_hash(hash_token(token))
        if session is None:
            raise AuthenticationError("unknown session")
        now = datetime.now(UTC)
        expires_at = to_utc(session.expires_at)
        last_activity = to_utc(session.last_activity_at)
        issued_at = to_utc(session.issued_at)
        if session.revoked_at is not None or expires_at is None or expires_at <= now:
            raise AuthenticationError("session revoked or expired")
        if last_activity is None or issued_at is None:
            raise AuthenticationError("session timestamps missing")
        inactivity = self.settings.get_int("session.inactivity_timeout_minutes", DEFAULT_INACTIVITY_MINUTES)
        if now - last_activity > timedelta(minutes=inactivity):
            self.sessions.revoke(session, now, "inactivity")
            raise AuthenticationError("session inactive")
        user = self.users.get_by_id(session.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("user inactive")
        self.sessions.touch(session, now)
        return CurrentUser(
            id=user.id,
            username=user.username,
            role=user.role,
            customer_id=user.customer_id,
            session_id=session.id,
            issued_at=issued_at,
            expires_at=expires_at,
            last_activity_at=now,
        )

    def logout(self, user: CurrentUser) -> None:
        session = self.db.get(UserSession, user.session_id)
        if session is None:
            return
        now = datetime.now(UTC)
        self.sessions.revoke(session, now, "logout")
        self.audit.record_committed(
            event_type="logout",
            entity_type="user_session",
            entity_id=str(session.id),
            actor_user_id=user.id,
            detail="logout",
        )

"""
Auth domain service - business logic for authentication.
"""
import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.orm import Session

from app.auth.auth_models import AppUser, UserSession
from app.auth.auth_repository import AuthRepository
from app.auth.auth_schemas import (
    CurrentUserResponse,
    LoginResponse,
    LogoutResponse,
    SessionRevokeResponse,
    StepUpResponse,
)
from app.core.errors import AuthenticationError, NotFoundError
from app.core.logging import get_logger
from app.core.security import verify_password
from app.core.settings import settings
from app.middleware.rate_limit import rate_limiter

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = AuthRepository(db)

    def _create_jwt_token(self, user_id: int, session_id: int) -> tuple[str, int]:
        """
        Create JWT token for user session.

        Args:
            user_id: User ID
            session_id: Session ID

        Returns:
            Tuple of (token, expires_in_seconds)
        """
        expires_in = settings.jwt_expiry_seconds
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        payload = {
            "sub": str(user_id),
            "session_id": str(session_id),
            "exp": expires_at,
            "iat": datetime.now(timezone.utc)
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        return token, expires_in

    def _hash_token(self, token: str) -> str:
        """
        Hash token for storage.

        Args:
            token: JWT token

        Returns:
            SHA-256 hash of token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def _determine_session_timeout(self, user: AppUser) -> int:
        """
        Determine session timeout based on risk profile.

        Args:
            user: User for session

        Returns:
            Timeout in seconds (900 for high-risk, 1800 for low-risk)
        """
        # High-risk: superuser = 900 seconds (15 minutes)
        # Low-risk: regular user = 1800 seconds (30 minutes)
        return 900 if user.is_superuser else 1800

    def login(self, email: str, password: str) -> LoginResponse:
        """
        Authenticate user and create session.

        Args:
            email: User email
            password: User password

        Returns:
            Login response with JWT token

        Raises:
            AuthenticationError: If authentication fails
        """
        # Check rate limit
        rate_limiter.check_rate_limit(email)

        # Get user
        user = self.repo.get_user_by_email(email)
        if not user:
            logger.warning("Login attempt for non-existent user", email=email)
            raise AuthenticationError(message="Invalid credentials")

        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning("Login attempt with invalid password", email=email)
            raise AuthenticationError(message="Invalid credentials")

        # Check if user is active
        if not user.is_active:
            logger.warning("Login attempt for inactive user", email=email)
            raise AuthenticationError(message="User account is inactive")

        # Reset rate limit on successful authentication
        rate_limiter.reset(email)

        # Determine session timeout
        timeout_seconds = self._determine_session_timeout(user)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=timeout_seconds)

        # Create temporary token for hashing (we'll generate the real one after session creation)
        temp_token = jwt.encode(
            {"sub": str(user.id), "temp": True},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        token_hash = self._hash_token(temp_token)

        # Create session
        session = self.repo.create_session(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )

        # Create actual JWT with session ID
        token, expires_in = self._create_jwt_token(user.id, session.id)

        # Update session with actual token hash
        session.token_hash = self._hash_token(token)
        self.db.commit()

        logger.info("User logged in successfully", user_id=user.id, session_id=session.id)

        # Build response
        user_response = CurrentUserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            session_id=session.id,
            session_expires_at=session.expires_at,
            step_up_verified_at=session.step_up_verified_at,
            selected_account_id=session.selected_account_id
        )

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            user=user_response
        )

    def logout(self, session_id: int) -> LogoutResponse:
        """
        Logout user by revoking session.

        Args:
            session_id: Session ID to revoke

        Returns:
            Logout response

        Raises:
            NotFoundError: If session not found
        """
        success = self.repo.revoke_session(session_id)

        if not success:
            raise NotFoundError(message="Session not found")

        logger.info("User logged out", session_id=session_id)

        return LogoutResponse(
            success=True,
            message="Logged out successfully"
        )

    def revoke_session(self, session_id: int, current_user_id: int) -> SessionRevokeResponse:
        """
        Revoke a specific session.

        Args:
            session_id: Session ID to revoke
            current_user_id: ID of user requesting revocation

        Returns:
            Session revoke response

        Raises:
            NotFoundError: If session not found
            AuthenticationError: If user doesn't own the session
        """
        session = self.repo.get_session_by_id(session_id)

        if not session:
            raise NotFoundError(message="Session not found")

        # Verify ownership (user can only revoke their own sessions)
        if session.user_id != current_user_id:
            raise AuthenticationError(message="Cannot revoke session belonging to another user")

        self.repo.revoke_session(session_id)

        logger.info("Session revoked", session_id=session_id, user_id=current_user_id)

        return SessionRevokeResponse(
            success=True,
            message="Session revoked successfully"
        )

    def step_up(self, user: AppUser, session: UserSession, password: str) -> StepUpResponse:
        """
        Perform step-up authentication for high-risk operations.

        Args:
            user: Current user
            session: Current session
            password: Password for verification

        Returns:
            Step-up response

        Raises:
            AuthenticationError: If password is invalid
        """
        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning("Step-up attempt with invalid password", user_id=user.id)
            raise AuthenticationError(message="Invalid credentials")

        # Update session with step-up timestamp
        success = self.repo.update_step_up(session.id)

        if not success:
            raise NotFoundError(message="Session not found")

        # Calculate validity (5 minutes = 300 seconds)
        valid_until = datetime.now(timezone.utc) + timedelta(seconds=300)

        logger.info("Step-up authentication successful", user_id=user.id, session_id=session.id)

        return StepUpResponse(
            success=True,
            message="Step-up authentication successful",
            valid_until=valid_until
        )

    def get_current_user_response(self, user: AppUser, session: UserSession) -> CurrentUserResponse:
        """
        Build current user response from user and session.

        Args:
            user: Current user
            session: Current session

        Returns:
            Current user response
        """
        return CurrentUserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            session_id=session.id,
            session_expires_at=session.expires_at,
            step_up_verified_at=session.step_up_verified_at,
            selected_account_id=session.selected_account_id
        )

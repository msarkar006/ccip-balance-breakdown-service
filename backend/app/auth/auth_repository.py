"""
Auth domain repository for database operations.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.auth.auth_models import AppUser, UserSession
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthRepository:
    """Repository for auth-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[AppUser]:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            User if found, None otherwise
        """
        return self.db.query(AppUser).filter(AppUser.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[AppUser]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        return self.db.query(AppUser).filter(AppUser.id == user_id).first()

    def create_session(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        selected_account_id: Optional[int] = None
    ) -> UserSession:
        """
        Create a new user session.

        Args:
            user_id: User ID
            token_hash: Hashed token
            expires_at: Session expiry timestamp
            selected_account_id: Selected account ID (optional)

        Returns:
            Created session
        """
        session = UserSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(session)
        self.db.flush()

        # Update selected account if provided
        if selected_account_id is not None:
            session.selected_account_id = selected_account_id

        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_id(self, session_id: int) -> Optional[UserSession]:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session if found, None otherwise
        """
        return self.db.query(UserSession).filter(UserSession.id == session_id).first()

    def revoke_session(self, session_id: int) -> bool:
        """
        Revoke a session.

        Args:
            session_id: Session ID to revoke

        Returns:
            True if session was revoked, False if not found
        """
        session = self.get_session_by_id(session_id)
        if not session:
            return False

        session.revoked_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def update_step_up(self, session_id: int) -> bool:
        """
        Update session with step-up verification timestamp.

        Args:
            session_id: Session ID

        Returns:
            True if updated, False if not found
        """
        session = self.get_session_by_id(session_id)
        if not session:
            return False

        session.step_up_verified_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def update_selected_account(self, session_id: int, account_id: Optional[int]) -> bool:
        """
        Update selected account for a session.

        Args:
            session_id: Session ID
            account_id: Account ID to select (or None to clear)

        Returns:
            True if updated, False if session not found
        """
        session = self.get_session_by_id(session_id)
        if not session:
            return False

        session.selected_account_id = account_id
        self.db.commit()
        return True

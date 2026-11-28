"""Parameterized access to `user_sessions`. Only the SHA-256 hash of a token is ever stored."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserSession


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class SessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self, user_id: uuid.UUID, token_hash: str, issued_at: datetime, expires_at: datetime
    ) -> UserSession:
        row = UserSession(
            user_id=user_id,
            token_hash=token_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            last_activity_at=issued_at,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def find_by_token_hash(self, token_hash: str) -> UserSession | None:
        return self.db.scalar(select(UserSession).where(UserSession.token_hash == token_hash))

    def touch(self, session: UserSession, when: datetime) -> None:
        session.last_activity_at = when
        self.db.commit()

    def revoke(self, session: UserSession, when: datetime, reason: str) -> None:
        """Revocation is committed in its own transaction so it survives a later rollback."""
        session.revoked_at = when
        session.revocation_reason = reason
        self.db.commit()

"""The single writer of `audit_log`. Never receives passwords, tokens or hashes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.middleware.correlation import get_correlation_id
from app.models import AuditLog
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuditRepository(db)

    def record(
        self,
        *,
        event_type: str,
        entity_type: str,
        severity: str = "info",
        entity_id: str | None = None,
        actor_user_id: uuid.UUID | None = None,
        detail: str | None = None,
    ) -> AuditLog:
        """Add a row in the caller's transaction (the caller commits)."""
        correlation_id = get_correlation_id()
        if correlation_id in ("", "-"):
            correlation_id = uuid.uuid4().hex
        return self.repo.add(
            AuditLog(
                occurred_at=datetime.now(UTC),
                severity=severity,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_user_id=actor_user_id,
                correlation_id=correlation_id,
                detail=detail[:500] if detail else None,
            )
        )

    def record_committed(self, **kwargs) -> AuditLog:  # type: ignore[no-untyped-def]
        """Add a row and commit it at once, so it survives the exception raised next."""
        entry = self.record(**kwargs)
        self.db.commit()
        return entry

"""Parameterized access to `tracking_events`, newest `occurred_at` first."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import TrackingEvent


class TrackingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_account(
        self, account_id: uuid.UUID, entity_type: str | None, limit: int, offset: int
    ) -> tuple[list[TrackingEvent], int]:
        conditions = [TrackingEvent.account_id == account_id]
        if entity_type is not None:
            conditions.append(TrackingEvent.tracked_entity_type == entity_type)
        total = self.db.scalar(select(func.count()).select_from(TrackingEvent).where(*conditions)) or 0
        stmt = (
            select(TrackingEvent)
            .where(*conditions)
            .order_by(TrackingEvent.occurred_at.desc(), TrackingEvent.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt)), total

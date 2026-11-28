"""Parameterized access to `cards`."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Card


class CardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_account(self, account_id: uuid.UUID, limit: int, offset: int) -> tuple[list[Card], int]:
        base = select(Card).where(Card.account_id == account_id)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = self.db.scalars(base.order_by(Card.source_ref, Card.id).limit(limit).offset(offset)).all()
        return list(rows), total

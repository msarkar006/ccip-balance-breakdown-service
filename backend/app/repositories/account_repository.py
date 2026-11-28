"""Parameterized access to `accounts`, always scoped to one customer."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Account


class AccountRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_customer(self, customer_id: uuid.UUID, limit: int, offset: int) -> tuple[list[Account], int]:
        base = select(Account).where(Account.customer_id == customer_id)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = self.db.scalars(base.order_by(Account.source_ref, Account.id).limit(limit).offset(offset)).all()
        return list(rows), total

    def get_for_customer(self, customer_id: uuid.UUID, account_id: uuid.UUID) -> Account | None:
        return self.db.scalar(
            select(Account).where(Account.id == account_id, Account.customer_id == customer_id)
        )

"""Parameterized access to `balance_breakdowns` and `balance_categories`."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Account, BalanceBreakdown, BalanceCategory


class BalanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_account(
        self, account_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[BalanceBreakdown], int]:
        base = select(BalanceBreakdown).where(BalanceBreakdown.account_id == account_id)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        # Null `as_of` last on both engines: the boolean sorts false (0) before true (1).
        rows = self.db.scalars(
            base.order_by(
                BalanceBreakdown.as_of.is_(None),
                BalanceBreakdown.as_of.desc(),
                BalanceBreakdown.source_ref,
                BalanceBreakdown.id,
            )
            .limit(limit)
            .offset(offset)
        ).all()
        return list(rows), total

    def get_for_customer(
        self, customer_id: uuid.UUID, breakdown_id: uuid.UUID
    ) -> BalanceBreakdown | None:
        return self.db.scalar(
            select(BalanceBreakdown)
            .join(Account, Account.id == BalanceBreakdown.account_id)
            .where(BalanceBreakdown.id == breakdown_id, Account.customer_id == customer_id)
        )

    def categories(self, breakdown_id: uuid.UUID) -> list[BalanceCategory]:
        return list(
            self.db.scalars(
                select(BalanceCategory)
                .where(BalanceCategory.breakdown_id == breakdown_id)
                .order_by(BalanceCategory.display_rank.asc())
            ).all()
        )

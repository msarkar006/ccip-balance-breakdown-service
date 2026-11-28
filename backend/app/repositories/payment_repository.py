"""Parameterized access to `payments`, newest payment date first."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Account, Payment


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_customer(self, customer_id: uuid.UUID, payment_id: uuid.UUID) -> Payment | None:
        stmt = (
            select(Payment)
            .join(Account, Account.id == Payment.account_id)
            .where(Payment.id == payment_id, Account.customer_id == customer_id)
        )
        return self.db.scalars(stmt).first()

    def list_for_account(
        self,
        account_id: uuid.UUID,
        payment_type: str | None,
        payment_status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Payment], int]:
        conditions = [Payment.account_id == account_id]
        if payment_type is not None:
            conditions.append(Payment.payment_type == payment_type)
        if payment_status is not None:
            conditions.append(Payment.payment_status == payment_status)
        total = self.db.scalar(select(func.count()).select_from(Payment).where(*conditions)) or 0
        stmt = (
            select(Payment)
            .where(*conditions)
            .order_by(Payment.payment_date.desc(), Payment.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt).all()), total

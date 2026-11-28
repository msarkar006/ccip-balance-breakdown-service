"""Parameterized access to `transactions`, left-joined to `cards` for the masked reference."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Account, Card, Transaction


class TransactionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_account(
        self, account_id: uuid.UUID, status: str | None, limit: int, offset: int
    ) -> tuple[list[tuple[Transaction, str | None]], int]:
        conditions = [Transaction.account_id == account_id]
        if status is not None:
            conditions.append(Transaction.transaction_status == status)
        total = self.db.scalar(select(func.count()).select_from(Transaction).where(*conditions)) or 0
        stmt = (
            select(Transaction, Card.masked_pan)
            .outerjoin(
                Card,
                (Card.id == Transaction.card_id) & (Card.account_id == Transaction.account_id),
            )
            .where(*conditions)
            .order_by(Transaction.transaction_time.desc(), Transaction.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [(row[0], row[1]) for row in self.db.execute(stmt).all()], total

    def get_for_customer(
        self, customer_id: uuid.UUID, transaction_id: uuid.UUID
    ) -> tuple[Transaction, str | None] | None:
        stmt = (
            select(Transaction, Card.masked_pan)
            .join(Account, Account.id == Transaction.account_id)
            .outerjoin(
                Card,
                (Card.id == Transaction.card_id) & (Card.account_id == Transaction.account_id),
            )
            .where(Transaction.id == transaction_id, Account.customer_id == customer_id)
        )
        row = self.db.execute(stmt).first()
        return (row[0], row[1]) if row else None

"""Transactions, payments and tracking events."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._columns import UTC_DATETIME, created_at_column, updated_at_column, utcnow, uuid_pk

MONEY = Numeric(14, 2)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_transactions"),
        UniqueConstraint("source_ref", name="uq_transactions_source_ref"),
        UniqueConstraint("id", "account_id", name="uq_transactions_id_account"),
        ForeignKeyConstraint(
            ["card_id", "account_id"],
            ["cards.id", "cards.account_id"],
            name="fk_transactions_card_account",
            ondelete="CASCADE",
        ),
        CheckConstraint("transaction_status IN ('Pending', 'Posted')", name="ck_transactions_status"),
        CheckConstraint(
            "merchant_category_code IS NULL OR length(merchant_category_code) = 4", name="ck_transactions_mcc"
        ),
        Index("ix_transactions_account_time", "account_id", "transaction_time"),
        Index("ix_transactions_card_id", "card_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", name="fk_transactions_account", ondelete="CASCADE"), nullable=False
    )
    card_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    source_ref: Mapped[str | None] = mapped_column(String(40))
    transaction_status: Mapped[str] = mapped_column(String(30), nullable=False)
    transaction_time: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    posted_date: Mapped[date | None] = mapped_column(Date)
    transaction_amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    merchant_name: Mapped[str | None] = mapped_column(String(100))
    merchant_category_code: Mapped[str | None] = mapped_column(String(4))
    eligible_for_instalment: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_payments"),
        UniqueConstraint("source_ref", name="uq_payments_source_ref"),
        UniqueConstraint("id", "account_id", name="uq_payments_id_account"),
        CheckConstraint(
            "payment_type IN ('OneOff', 'Scheduled', 'DirectDebitCollection')", name="ck_payments_type"
        ),
        CheckConstraint(
            "payment_method IN ('FasterPayments', 'DebitCard', 'DirectDebit')", name="ck_payments_method"
        ),
        CheckConstraint(
            "payment_status IN ('Completed', 'Processing', 'Failed', 'Submitted', 'Cancelled')",
            name="ck_payments_status",
        ),
        CheckConstraint("payment_amount >= 0", name="ck_payments_amount"),
        CheckConstraint(
            "source_masked_account IS NULL OR source_masked_account LIKE '****%'", name="ck_payments_masked"
        ),
        Index("ix_payments_account_date", "account_id", "payment_date"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", name="fk_payments_account", ondelete="CASCADE"), nullable=False
    )
    source_ref: Mapped[str | None] = mapped_column(String(40))
    via_mandate_ref: Mapped[str | None] = mapped_column(String(40))
    payment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_bank_name: Mapped[str | None] = mapped_column(String(100))
    source_masked_account: Mapped[str | None] = mapped_column(String(12))
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_tracking_events"),
        ForeignKeyConstraint(
            ["transaction_id", "account_id"],
            ["transactions.id", "transactions.account_id"],
            name="fk_tracking_events_transaction",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["payment_id", "account_id"],
            ["payments.id", "payments.account_id"],
            name="fk_tracking_events_payment",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "tracked_entity_type IN ('account', 'transaction', 'payment')", name="ck_tracking_events_type"
        ),
        CheckConstraint("length(lifecycle_status) > 0", name="ck_tracking_events_status_nonblank"),
        CheckConstraint(
            "(tracked_entity_type = 'account' AND transaction_id IS NULL AND payment_id IS NULL "
            "AND tracked_entity_id = account_id) "
            "OR (tracked_entity_type = 'transaction' AND transaction_id IS NOT NULL AND payment_id IS NULL "
            "AND tracked_entity_id = transaction_id) "
            "OR (tracked_entity_type = 'payment' AND payment_id IS NOT NULL AND transaction_id IS NULL "
            "AND tracked_entity_id = payment_id)",
            name="ck_tracking_events_target",
        ),
        Index("ix_tracking_events_account_occurred", "account_id", "occurred_at"),
        Index("ix_tracking_events_transaction_id", "transaction_id"),
        Index("ix_tracking_events_payment_id", "payment_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", name="fk_tracking_events_account", ondelete="CASCADE"), nullable=False
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    tracked_entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    tracked_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(40), nullable=False)
    source_time: Mapped[datetime | None] = mapped_column(UTC_DATETIME)
    provenance: Mapped[str] = mapped_column(String(100), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        UTC_DATETIME, nullable=False, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )


__all__ = ["Payment", "TrackingEvent", "Transaction", "created_at_column", "updated_at_column"]

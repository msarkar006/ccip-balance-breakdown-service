"""Account, card, balance breakdown and balance category tables."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._columns import UTC_DATETIME, created_at_column, updated_at_column, uuid_pk

MONEY = Numeric(14, 2)
RATE = Numeric(7, 3)


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_accounts"),
        UniqueConstraint("source_ref", name="uq_accounts_source_ref"),
        CheckConstraint("length(account_status) > 0", name="ck_accounts_status_nonblank"),
        CheckConstraint("length(currency) = 3", name="ck_accounts_currency"),
        CheckConstraint("credit_limit IS NULL OR credit_limit >= 0", name="ck_accounts_credit_limit"),
        CheckConstraint(
            "available_credit IS NULL OR available_credit >= 0", name="ck_accounts_available_credit"
        ),
        CheckConstraint(
            "standard_purchase_apr IS NULL OR (standard_purchase_apr >= 0 AND standard_purchase_apr <= 100)",
            name="ck_accounts_apr",
        ),
        CheckConstraint("minimum_payment IS NULL OR minimum_payment >= 0", name="ck_accounts_min_payment"),
        Index("ix_accounts_customer_id", "customer_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("customers.id", name="fk_accounts_customer", ondelete="CASCADE"), nullable=False
    )
    source_ref: Mapped[str | None] = mapped_column(String(40))
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_status: Mapped[str] = mapped_column(String(40), nullable=False)
    opened_on: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    credit_limit: Mapped[Decimal | None] = mapped_column(MONEY)
    available_credit: Mapped[Decimal | None] = mapped_column(MONEY)
    current_balance: Mapped[Decimal | None] = mapped_column(MONEY)
    standard_purchase_apr: Mapped[Decimal | None] = mapped_column(RATE)
    last_statement_balance: Mapped[Decimal | None] = mapped_column(MONEY)
    next_statement_date: Mapped[date | None] = mapped_column(Date)
    payment_due_date: Mapped[date | None] = mapped_column(Date)
    minimum_payment: Mapped[Decimal | None] = mapped_column(MONEY)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_cards"),
        UniqueConstraint("source_ref", name="uq_cards_source_ref"),
        UniqueConstraint("id", "account_id", name="uq_cards_id_account"),
        CheckConstraint("masked_pan LIKE '****%'", name="ck_cards_masked"),
        CheckConstraint("card_status IN ('Active', 'PendingActivation')", name="ck_cards_status"),
        CheckConstraint("expiry_month_year IS NULL OR length(expiry_month_year) = 7", name="ck_cards_expiry"),
        Index("ix_cards_account_id", "account_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", name="fk_cards_account", ondelete="CASCADE"), nullable=False
    )
    source_ref: Mapped[str | None] = mapped_column(String(40))
    masked_pan: Mapped[str] = mapped_column(String(12), nullable=False)
    card_status: Mapped[str] = mapped_column(String(30), nullable=False)
    expiry_month_year: Mapped[str | None] = mapped_column(String(7))
    is_digital: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class BalanceBreakdown(Base):
    __tablename__ = "balance_breakdowns"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_balance_breakdowns"),
        UniqueConstraint("source_ref", name="uq_balance_breakdowns_source_ref"),
        CheckConstraint(
            "total_outstanding IS NULL OR total_outstanding >= 0", name="ck_balance_breakdowns_outstanding"
        ),
        CheckConstraint("pending_total IS NULL OR pending_total >= 0", name="ck_balance_breakdowns_pending"),
        CheckConstraint(
            "purchases_subtotal IS NULL OR purchases_subtotal >= 0", name="ck_balance_breakdowns_purchases"
        ),
        CheckConstraint(
            "balance_transfers_subtotal IS NULL OR balance_transfers_subtotal >= 0",
            name="ck_balance_breakdowns_bt",
        ),
        Index("ix_balance_breakdowns_account_asof", "account_id", "as_of"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", name="fk_balance_breakdowns_account", ondelete="CASCADE"),
        nullable=False,
    )
    source_ref: Mapped[str | None] = mapped_column(String(40))
    as_of: Mapped[datetime | None] = mapped_column(UTC_DATETIME)
    total_outstanding: Mapped[Decimal | None] = mapped_column(MONEY)
    pending_total: Mapped[Decimal | None] = mapped_column(MONEY)
    is_zero_balance: Mapped[bool | None] = mapped_column(Boolean)
    purchases_subtotal: Mapped[Decimal | None] = mapped_column(MONEY)
    balance_transfers_subtotal: Mapped[Decimal | None] = mapped_column(MONEY)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class BalanceCategory(Base):
    __tablename__ = "balance_categories"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_balance_categories"),
        UniqueConstraint("source_ref", name="uq_balance_categories_source_ref"),
        UniqueConstraint("breakdown_id", "display_rank", name="uq_balance_categories_rank"),
        CheckConstraint(
            "category_type IN ('StandardPurchase', 'PromotionalPurchase', 'BalanceTransfer', 'Instalment')",
            name="ck_balance_categories_type",
        ),
        CheckConstraint("display_rank >= 1", name="ck_balance_categories_rank"),
        CheckConstraint(
            "category_balance IS NULL OR category_balance >= 0", name="ck_balance_categories_balance"
        ),
        CheckConstraint(
            "category_apr_percent IS NULL OR (category_apr_percent >= 0 AND category_apr_percent <= 100)",
            name="ck_balance_categories_apr",
        ),
        CheckConstraint(
            "revert_rate_percent IS NULL OR (revert_rate_percent >= 0 AND revert_rate_percent <= 100)",
            name="ck_balance_categories_revert",
        ),
        CheckConstraint("days_to_expiry IS NULL OR days_to_expiry >= 0", name="ck_balance_categories_days"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    breakdown_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("balance_breakdowns.id", name="fk_balance_categories_breakdown", ondelete="CASCADE"),
        nullable=False,
    )
    source_ref: Mapped[str | None] = mapped_column(String(40))
    category_type: Mapped[str] = mapped_column(String(30), nullable=False)
    category_label: Mapped[str] = mapped_column(String(100), nullable=False)
    display_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    category_balance: Mapped[Decimal | None] = mapped_column(MONEY)
    category_apr_percent: Mapped[Decimal | None] = mapped_column(RATE)
    promo_end_date: Mapped[date | None] = mapped_column(Date)
    revert_rate_percent: Mapped[Decimal | None] = mapped_column(RATE)
    days_to_expiry: Mapped[int | None] = mapped_column(Integer)
    source_balance_transfer_ref: Mapped[str | None] = mapped_column(String(40))
    source_instalment_plan_ref: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

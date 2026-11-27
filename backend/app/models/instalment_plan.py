"""
InstalmentPlan model - instalment plans for transactions.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class InstalmentPlan(Base):
    """Instalment plan record."""

    __tablename__ = "instalment_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("credit_card_accounts.id"), nullable=False, index=True)
    plan_reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    remaining_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    instalment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_payment: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    apr: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

"""
CreditCardAccount model - customer credit card account.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class CreditCardAccount(Base):
    """Credit card account owned by a customer."""

    __tablename__ = "credit_card_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    account_number_masked: Mapped[str] = mapped_column(String(20), nullable=False)
    sort_code_masked: Mapped[str] = mapped_column(String(10), nullable=False)
    account_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    available_credit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    minimum_payment_due: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    payment_due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

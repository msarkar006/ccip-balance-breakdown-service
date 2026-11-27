"""
DirectDebitMandate model - direct debit agreements.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class DirectDebitMandate(Base):
    """Direct debit mandate record."""

    __tablename__ = "direct_debit_mandates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("credit_card_accounts.id"), nullable=False, index=True)
    mandate_reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    mandate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

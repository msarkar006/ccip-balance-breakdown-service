"""
CreditCard model - physical/virtual card linked to account.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class CreditCard(Base):
    """Credit card (physical or virtual) linked to an account."""

    __tablename__ = "credit_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("credit_card_accounts.id"), nullable=False, index=True)
    card_number_masked: Mapped[str] = mapped_column(String(20), nullable=False)
    card_type: Mapped[str] = mapped_column(String(20), nullable=False)
    card_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    expiry_month: Mapped[int] = mapped_column(Integer, nullable=False)
    expiry_year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

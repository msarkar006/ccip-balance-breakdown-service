"""
BalanceCategory model - detailed balance category entries.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class BalanceCategory(Base):
    """Balance category within a breakdown."""

    __tablename__ = "balance_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    breakdown_id: Mapped[int] = mapped_column(Integer, ForeignKey("balance_breakdowns.id"), nullable=False, index=True)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    apr: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    display_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    promo_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    promo_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_balance_transfer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("balance_transfers.id"), nullable=True, index=True)
    source_instalment_plan_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("instalment_plans.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

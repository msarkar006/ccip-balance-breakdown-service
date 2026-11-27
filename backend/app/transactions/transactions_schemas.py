"""
Transaction schemas - request/response models for transaction endpoints.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TransactionResponse(BaseModel):
    """Single transaction response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    external_transaction_id: str
    transaction_date: datetime = Field(description="Transaction datetime")
    posting_date: Optional[datetime] = Field(None, description="Posted date (null if Pending)")
    merchant_name: str
    transaction_type: str
    amount: Decimal
    currency: str
    status: str = Field(description="Transaction status: Pending, Posted, StatusUnavailable")
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    """Paginated transaction list response with envelope."""

    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
    empty_state_message: Optional[str] = None
    freshness: dict = Field(default_factory=lambda: {"level": "Current", "as_of": None})

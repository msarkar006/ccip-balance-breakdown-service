"""
Rewards, offers, and instalments schemas - request/response models.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class OfferListItem(BaseModel):
    """Single offer item in list response."""

    id: int
    offer_code: str
    offer_title: str
    offer_description: Optional[str] = None
    offer_type: str
    status: str
    valid_from: datetime
    valid_until: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OfferListResponse(BaseModel):
    """Paginated offer list response."""

    items: list[OfferListItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class OfferDetailResponse(BaseModel):
    """Detailed offer information."""

    id: int
    account_id: int
    offer_code: str
    offer_title: str
    offer_description: Optional[str] = None
    offer_type: str
    status: str
    valid_from: datetime
    valid_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InstalmentPlanListItem(BaseModel):
    """Single instalment plan item in list response."""

    id: int
    plan_reference: str
    plan_name: str
    original_amount: Decimal
    remaining_balance: Decimal
    instalment_count: int
    monthly_payment: Decimal
    apr: Optional[Decimal] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InstalmentPlanListResponse(BaseModel):
    """Paginated instalment plan list response."""

    items: list[InstalmentPlanListItem]
    total: int
    limit: int
    offset: int
    has_more: bool
    empty_state_message: Optional[str] = None


class SourceTransaction(BaseModel):
    """Source transaction detail for instalment plan."""

    transaction_id: int
    external_transaction_id: str
    merchant_name: str
    transaction_date: datetime
    amount: Decimal


class LinkedBalanceCategory(BaseModel):
    """Linked balance category information."""

    category_id: int
    category_name: str
    category_amount: Decimal


class BalanceEffect(BaseModel):
    """Balance effect explanation."""

    is_reflected_in_balance: bool
    explanation: str


class InstalmentPlanDetailResponse(BaseModel):
    """Detailed instalment plan information with context."""

    id: int
    account_id: int
    plan_reference: str
    plan_name: str
    original_amount: Decimal
    remaining_balance: Decimal
    instalment_count: int
    monthly_payment: Decimal
    apr: Optional[Decimal] = None
    status: str
    source_transaction: Optional[SourceTransaction] = None
    linked_category: Optional[LinkedBalanceCategory] = None
    balance_effect: BalanceEffect
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

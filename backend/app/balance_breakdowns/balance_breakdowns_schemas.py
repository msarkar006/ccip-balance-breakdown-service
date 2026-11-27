"""
Balance breakdown request/response schemas.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FreshnessInfo(BaseModel):
    """Freshness disclosure information."""

    level: str = Field(..., description="Freshness level: Current, Stale, Unknown")
    as_of: datetime = Field(..., description="Timestamp when data was last synchronized")

    model_config = ConfigDict(from_attributes=True)


class SourceLink(BaseModel):
    """Source linkage for balance categories."""

    source_type: str = Field(..., description="Type of source: BalanceTransfer or InstalmentPlan")
    source_id: int = Field(..., description="ID of the source entity")
    source_reference: Optional[str] = Field(None, description="External reference if available")

    model_config = ConfigDict(from_attributes=True)


class BalanceCategoryItem(BaseModel):
    """Balance category item in breakdown list."""

    id: int
    category_name: str
    category_amount: Decimal
    apr: Optional[Decimal] = None
    display_rank: Optional[int] = None
    promo_rate: Optional[Decimal] = None
    promo_end_date: Optional[datetime] = None
    source_link: Optional[SourceLink] = None

    model_config = ConfigDict(from_attributes=True)


class BalanceBreakdownResponse(BaseModel):
    """Balance breakdown response with categories and freshness."""

    id: int
    account_id: int
    total_balance: Decimal
    pending_total: Decimal = Field(..., description="Sum of pending/unposted amounts")
    snapshot_date: datetime
    categories: list[BalanceCategoryItem]
    freshness: FreshnessInfo
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryDetailResponse(BaseModel):
    """Detailed category view with full context."""

    id: int
    breakdown_id: int
    category_name: str
    category_amount: Decimal
    apr: Optional[Decimal] = None
    display_rank: Optional[int] = None
    promo_rate: Optional[Decimal] = None
    promo_end_date: Optional[datetime] = None
    source_link: Optional[SourceLink] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

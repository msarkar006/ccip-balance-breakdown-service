"""
Balance transfer request/response schemas.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TrackerMilestone(BaseModel):
    """Tracking milestone/event in transfer lifecycle."""

    event_type: str = Field(..., description="Event type")
    status: str = Field(..., description="Status at this milestone")
    occurred_at: datetime = Field(..., description="When this event occurred")
    event_data: Optional[str] = Field(None, description="Additional event context")

    model_config = ConfigDict(from_attributes=True)


class PromotionalContext(BaseModel):
    """Promotional offer context for balance transfer."""

    promo_rate: Optional[Decimal] = Field(None, description="Promotional APR")
    promo_start_date: Optional[datetime] = Field(None, description="Promotional period start date")
    promo_end_date: Optional[datetime] = Field(None, description="Promotional period end date")
    revert_rate: Optional[Decimal] = Field(None, description="APR after promotional period")

    model_config = ConfigDict(from_attributes=True)


class SourceLink(BaseModel):
    """Source linkage to balance category."""

    source_type: str = Field(..., description="Always 'BalanceTransfer' for this context")
    source_id: int = Field(..., description="ID of this balance transfer")
    source_reference: str = Field(..., description="External transfer reference")
    category_id: Optional[int] = Field(None, description="Linked balance category ID if applicable")
    category_name: Optional[str] = Field(None, description="Linked balance category name if applicable")

    model_config = ConfigDict(from_attributes=True)


class GuidanceInfo(BaseModel):
    """Guidance for Rejected or unresolved transfers."""

    message_code: str = Field(..., description="Guidance message code")
    message: str = Field(..., description="Human-readable guidance message")
    next_step: Optional[str] = Field(None, description="Recommended next action")

    model_config = ConfigDict(from_attributes=True)


class BalanceTransferListItem(BaseModel):
    """Balance transfer item in paginated history."""

    id: int
    external_transfer_id: str
    transfer_amount: Decimal
    promotional_rate: Optional[Decimal] = None
    status: str
    requested_on: datetime = Field(..., description="When the transfer was created")
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BalanceTransferListResponse(BaseModel):
    """Paginated balance transfer history response."""

    items: list[BalanceTransferListItem]
    total: int
    limit: int
    offset: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)


class BalanceTransferDetailResponse(BaseModel):
    """Detailed balance transfer response with timeline and promotional context."""

    id: int
    account_id: int
    external_transfer_id: str
    transfer_amount: Decimal
    status: str
    requested_on: datetime = Field(..., description="When the transfer was created")
    processed_at: Optional[datetime] = None
    timeline: list[TrackerMilestone] = Field(..., description="Tracking events ordered by occurred_at ASC")
    promotional_context: Optional[PromotionalContext] = Field(None, description="Promotional offer details")
    source_link: Optional[SourceLink] = Field(None, description="Linkage to balance category")
    guidance: Optional[GuidanceInfo] = Field(None, description="Guidance for Rejected/unresolved transfers")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BalanceTransferInitiationRequest(BaseModel):
    """Request to initiate a balance transfer."""

    account_id: int = Field(..., description="Account ID")
    offer_code: str = Field(..., description="Selected offer code")
    transfer_amount: Decimal = Field(..., description="Transfer amount", gt=0)
    external_card_last4: str = Field(..., description="Last 4 digits of external card", min_length=4, max_length=4)
    provider_name: str = Field(..., description="External card provider name")
    idempotency_key: str = Field(..., description="Unique idempotency key for this request")


class BalanceTransferInitiationResponse(BaseModel):
    """Response after balance transfer initiation."""

    id: int
    external_transfer_id: str
    transfer_amount: Decimal
    status: str = Field(..., description="Outcome status: Submitted, ReviewRequired, or Rejected")
    guidance: Optional[GuidanceInfo] = Field(None, description="Guidance when submission cannot complete")
    idempotent_replay: bool = Field(False, description="True if this was an idempotent replay")

    model_config = ConfigDict(from_attributes=True)

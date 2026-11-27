"""
Money transfer request/response schemas.
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


class PayeeInfo(BaseModel):
    """Payee information for money transfer."""

    payee_id: int
    payee_name: str
    account_number_masked: str
    sort_code_masked: str

    model_config = ConfigDict(from_attributes=True)


class GuidanceInfo(BaseModel):
    """Guidance for Failed, Rejected, Delayed, or Blocked transfers."""

    message_code: str = Field(..., description="Guidance message code")
    message: str = Field(..., description="Human-readable guidance message")
    next_step: Optional[str] = Field(None, description="Recommended next action")

    model_config = ConfigDict(from_attributes=True)


class MoneyTransferListItem(BaseModel):
    """Money transfer item in paginated history."""

    id: int
    external_transfer_id: str
    payee_name: str = Field(..., description="Payee name from linked payee")
    amount: Decimal
    currency: str
    status: str
    requested_on: datetime = Field(..., description="When the transfer was created")
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MoneyTransferListResponse(BaseModel):
    """Paginated money transfer history response."""

    items: list[MoneyTransferListItem]
    total: int
    limit: int
    offset: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)


class MoneyTransferDetailResponse(BaseModel):
    """Detailed money transfer response with timeline and guidance."""

    id: int
    account_id: int
    external_transfer_id: str
    payee: PayeeInfo = Field(..., description="Payee details")
    amount: Decimal
    currency: str
    fee_context: Optional[str] = Field(None, description="Fee context if available")
    status: str
    requested_on: datetime = Field(..., description="When the transfer was created")
    processed_at: Optional[datetime] = None
    timeline: list[TrackerMilestone] = Field(..., description="Tracking events ordered by occurred_at ASC")
    guidance: Optional[GuidanceInfo] = Field(None, description="Guidance for Failed/Delayed/Blocked transfers")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PayeeListItem(BaseModel):
    """Payee item in paginated list."""

    id: int
    payee_name: str
    account_number_masked: str
    sort_code_masked: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PayeeListResponse(BaseModel):
    """Paginated payee list response."""

    items: list[PayeeListItem]
    total: int
    limit: int
    offset: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)


class MoneyTransferInitiationRequest(BaseModel):
    """Request to initiate a money transfer."""

    account_id: int = Field(..., description="Account ID")
    payee_id: int = Field(..., description="Selected payee ID")
    amount: Decimal = Field(..., description="Transfer amount", gt=0)
    currency: str = Field("GBP", description="Currency code")
    idempotency_key: str = Field(..., description="Unique idempotency key for this request")


class MoneyTransferInitiationResponse(BaseModel):
    """Response after money transfer initiation."""

    id: int
    external_transfer_id: str
    amount: Decimal
    currency: str
    status: str = Field(..., description="Outcome status: Submitted, Processing, Rejected, Failed, or Blocked")
    guidance: Optional[GuidanceInfo] = Field(None, description="Guidance when submission cannot complete")
    idempotent_replay: bool = Field(False, description="True if this was an idempotent replay")

    model_config = ConfigDict(from_attributes=True)

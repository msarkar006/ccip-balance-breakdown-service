"""
Payment schemas - request/response models for payment endpoints.
"""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    pass


class TrackerMilestone(BaseModel):
    """Single tracking event milestone."""

    event_type: str
    status: str
    event_timestamp: datetime
    description: Optional[str] = None


class PaymentResponse(BaseModel):
    """Single payment response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    external_payment_id: str
    idempotency_key: Optional[str] = None
    payment_method: str
    amount: Decimal
    currency: str
    status: str = Field(description="Payment status: Submitted, Processing, Completed, Failed, Cancelled, Restricted")
    scheduled_date: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PaymentDetailResponse(BaseModel):
    """Detailed payment response with timeline."""

    payment: PaymentResponse
    timeline: list[TrackerMilestone] = Field(default_factory=list, description="Tracking events ordered by event_timestamp ASC")
    can_cancel: bool = Field(description="Whether payment can be cancelled")
    cancellation_message: Optional[str] = Field(None, description="Explanation if cancellation not available")
    guidance: Optional[dict] = Field(None, description="Next-step guidance for non-final/failed payments")


class PaymentListResponse(BaseModel):
    """Paginated payment list response with envelope."""

    items: list[PaymentResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
    empty_state_message: Optional[str] = None
    freshness: dict = Field(default_factory=lambda: {"level": "Current", "as_of": None})


class PaymentInitiationRequest(BaseModel):
    """Request to initiate a payment."""

    account_id: int
    amount: Decimal = Field(..., gt=0, description="Payment amount (must be > 0)")
    currency: str = Field(default="GBP", description="Currency code")
    payment_method: str = Field(default="BankTransfer", description="Payment method")
    scheduled_date: Optional[datetime] = Field(None, description="Optional scheduled date for future payment")
    idempotency_key: str = Field(..., description="Client-generated idempotency key")


class PaymentGuidanceResponse(BaseModel):
    """Payment guidance with balance and direct debit coverage."""

    minimum_payment: Decimal
    due_date: Optional[datetime]
    current_balance: Decimal
    max_payment_amount: Decimal
    direct_debit_coverage: dict  # Will contain DirectDebitCoverageResponse data


class PaymentInitiationResponse(BaseModel):
    """Response after initiating a payment."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    external_payment_id: str
    idempotency_key: Optional[str]
    amount: Decimal
    currency: str
    status: str
    scheduled_date: Optional[datetime]
    created_at: datetime
    guidance: Optional[dict] = Field(None, description="Guidance for non-allow outcomes")


class PaymentCancellationResponse(BaseModel):
    """Response after cancelling a payment."""

    payment_id: int
    status: str = Field(description="Payment status after cancellation (should be 'Cancelled')")
    message: str = Field(description="Cancellation confirmation message")
    cancelled_at: datetime = Field(description="Timestamp when payment was cancelled")

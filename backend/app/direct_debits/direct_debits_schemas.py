"""
Direct debit schemas for request/response models.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DirectDebitListItem(BaseModel):
    """Single direct debit mandate item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    mandate_reference: str
    mandate_type: str
    payment_amount: Optional[Decimal]
    status: str
    activated_at: Optional[datetime]
    created_at: datetime


class DirectDebitListResponse(BaseModel):
    """List of direct debit mandates for an account."""

    mandates: List[DirectDebitListItem]


class DirectDebitCoverageResponse(BaseModel):
    """
    Direct debit coverage assessment.
    
    Indicates whether active direct debit is expected to cover minimum payment.
    """

    coverage_status: str = Field(
        ...,
        description="Coverage status: expected_to_cover, not_expected_to_cover, cannot_be_confirmed"
    )
    manual_payment_may_be_required: bool = Field(
        ...,
        description="Flag indicating manual payment may still be needed"
    )
    reason: Optional[str] = Field(
        None,
        description="Explanation for coverage status"
    )


class ChangeRequestRequest(BaseModel):
    """Request to initiate a direct debit change."""

    mandate_id: int
    change_type: str = Field(
        ...,
        description="Change type: Amend, Cancel, Reinstate"
    )
    new_payment_amount: Optional[Decimal] = Field(
        None,
        description="New payment amount for Amend change type"
    )
    idempotency_key: str = Field(
        ...,
        description="Client-generated idempotency key"
    )


class ChangeRequestResponse(BaseModel):
    """Response after initiating a direct debit change."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    mandate_id: int
    change_type: str
    new_payment_amount: Optional[Decimal]
    status: str
    created_at: datetime

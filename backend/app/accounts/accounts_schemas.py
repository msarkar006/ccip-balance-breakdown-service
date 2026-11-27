"""
Accounts domain schemas for request/response models.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AccountListItem(BaseModel):
    """Account list item response."""

    id: int = Field(..., description="Account ID")
    account_number_masked: str = Field(..., description="Masked account number")
    account_status: str = Field(..., description="Account status")
    current_balance: Decimal = Field(..., description="Current balance")
    available_credit: Decimal = Field(..., description="Available credit")
    credit_limit: Decimal = Field(..., description="Credit limit")

    model_config = ConfigDict(from_attributes=True)


class AccountListResponse(BaseModel):
    """List of accounts response."""

    accounts: List[AccountListItem] = Field(..., description="List of accounts")


class CreditCardDetail(BaseModel):
    """Credit card detail."""

    id: int = Field(..., description="Card ID")
    card_number_masked: str = Field(..., description="Masked card number")
    card_type: str = Field(..., description="Card type (e.g., Visa, Mastercard)")
    card_status: str = Field(..., description="Card status")
    expiry_month: int = Field(..., description="Expiry month")
    expiry_year: int = Field(..., description="Expiry year")

    model_config = ConfigDict(from_attributes=True)


class AccountOverviewResponse(BaseModel):
    """Account overview response with detailed information."""

    id: int = Field(..., description="Account ID")
    account_number_masked: str = Field(..., description="Masked account number")
    sort_code_masked: str = Field(..., description="Masked sort code")
    account_status: str = Field(..., description="Account status")
    credit_limit: Decimal = Field(..., description="Credit limit")
    available_credit: Decimal = Field(..., description="Available credit")
    current_balance: Decimal = Field(..., description="Current balance")
    minimum_payment_due: Decimal = Field(..., description="Minimum payment due")
    payment_due_date: Optional[datetime] = Field(None, description="Payment due date")
    cards: List[CreditCardDetail] = Field(..., description="Associated cards")
    freshness: str = Field(..., description="Data freshness indicator")
    as_of: datetime = Field(..., description="Data as-of timestamp")

    model_config = ConfigDict(from_attributes=True)


class AccountSelectionRequest(BaseModel):
    """Account selection request."""

    account_id: Optional[int] = Field(None, description="Account ID to select (null to clear)")


class AccountSelectionResponse(BaseModel):
    """Account selection response."""

    success: bool = Field(..., description="Whether selection was successful")
    selected_account_id: Optional[int] = Field(None, description="Selected account ID")
    message: str = Field(..., description="Response message")

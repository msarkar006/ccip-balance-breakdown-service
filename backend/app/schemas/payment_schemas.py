"""Payment response schemas: source type, method and status verbatim; source account masked."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field

from app.schemas.account_schemas import MoneyNullable
from app.schemas.common_schemas import ApiModel, Freshness, Page
from app.utils import mask_check

PaymentType = Literal["OneOff", "Scheduled", "DirectDebitCollection"]
PaymentMethod = Literal["FasterPayments", "DebitCard", "DirectDebit"]
PaymentStatus = Literal["Completed", "Processing", "Failed", "Submitted", "Cancelled"]
MaskedAccount = Annotated[str, Field(max_length=12, pattern=r"^\*\*\*\*")]
MaskedAccountNullable = Annotated[MaskedAccount | None, BeforeValidator(mask_check)]


class PaymentOut(ApiModel):
    id: uuid.UUID
    account_id: uuid.UUID
    source_ref: str | None = Field(default=None, max_length=40)
    via_mandate_ref: str | None = Field(default=None, max_length=40)
    payment_type: PaymentType
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    payment_amount: MoneyNullable
    payment_date: date
    source_bank_name: str | None = Field(default=None, max_length=100)
    source_masked_account: MaskedAccountNullable = None
    freshness: Freshness
    informational_notice: str


PaymentPage = Page[PaymentOut]

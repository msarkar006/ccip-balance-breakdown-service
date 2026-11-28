"""Transaction response schemas: source status and dates verbatim, card reference masked."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field

from app.schemas.account_schemas import MoneyNullable
from app.schemas.common_schemas import ApiModel, Freshness, Page
from app.utils import mask_check

TransactionStatus = Literal["Pending", "Posted"]
MaskedPan = Annotated[str, Field(max_length=12, pattern=r"^\*\*\*\*")]
MaskedPanNullable = Annotated[MaskedPan | None, BeforeValidator(mask_check)]


class TransactionOut(ApiModel):
    id: uuid.UUID
    account_id: uuid.UUID
    card_id: uuid.UUID | None = None
    masked_pan: MaskedPanNullable = None
    source_ref: str | None = Field(default=None, max_length=40)
    transaction_status: TransactionStatus
    transaction_time: datetime
    posted_date: date | None = None
    transaction_amount: MoneyNullable
    merchant_name: str | None = None
    merchant_category_code: str | None = Field(default=None, min_length=4, max_length=4)
    eligible_for_instalment: bool | None = None
    freshness: Freshness


TransactionPage = Page[TransactionOut]

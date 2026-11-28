"""Account response schemas. Money and percent are strings; absent values stay null."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BeforeValidator

from app.schemas.common_schemas import ApiModel, Freshness, Page


def _money(value: object) -> object:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return value


def _percent(value: object) -> object:
    if isinstance(value, Decimal):
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        return text or "0"
    return value


MoneyNullable = Annotated[str | None, BeforeValidator(_money)]
PercentNullable = Annotated[str | None, BeforeValidator(_percent)]


class AccountOut(ApiModel):
    id: uuid.UUID
    source_ref: str | None
    product_name: str
    account_status: str
    opened_on: date | None
    currency: str
    credit_limit: MoneyNullable
    available_credit: MoneyNullable
    current_balance: MoneyNullable
    standard_purchase_apr: PercentNullable
    last_statement_balance: MoneyNullable
    next_statement_date: date | None
    payment_due_date: date | None
    minimum_payment: MoneyNullable
    freshness: Freshness
    informational_notice: str


AccountPage = Page[AccountOut]

"""Balance breakdown response schemas. Values are copied from the source row, never computed."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from app.schemas.account_schemas import MoneyNullable, PercentNullable
from app.schemas.common_schemas import ApiModel, Freshness, Page


class BalanceCategoryOut(ApiModel):
    id: uuid.UUID
    source_ref: str | None = None
    category_type: str
    category_label: str
    display_rank: int
    category_balance: MoneyNullable = None
    category_apr_percent: PercentNullable = None
    promo_end_date: date | None = None
    revert_rate_percent: PercentNullable = None
    days_to_expiry: int | None = None
    source_balance_transfer_ref: str | None = None
    source_instalment_plan_ref: str | None = None
    qualifier_notice: str | None = None


class BalanceBreakdownSummaryOut(ApiModel):
    id: uuid.UUID
    account_id: uuid.UUID
    source_ref: str | None = None
    as_of: datetime | None = None
    total_outstanding: MoneyNullable = None
    pending_total: MoneyNullable = None
    is_zero_balance: bool | None = None
    freshness: Freshness


class BalanceBreakdownOut(ApiModel):
    id: uuid.UUID
    account_id: uuid.UUID
    source_ref: str | None = None
    as_of: datetime | None = None
    total_outstanding: MoneyNullable = None
    pending_total: MoneyNullable = None
    is_zero_balance: bool | None = None
    purchases_subtotal: MoneyNullable = None
    balance_transfers_subtotal: MoneyNullable = None
    categories: list[BalanceCategoryOut]
    freshness: Freshness
    notice: str


BalanceBreakdownPage = Page[BalanceBreakdownSummaryOut]

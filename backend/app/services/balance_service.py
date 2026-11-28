"""Balance breakdown rules: stored values verbatim, `asOf` never now, pending never relabelled."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import BalanceBreakdown, BalanceCategory
from app.policy import InformationOnlyPolicy
from app.repositories.account_repository import AccountRepository
from app.repositories.balance_repository import BalanceRepository
from app.repositories.setting_repository import SettingsRepository
from app.schemas.balance_schemas import (
    BalanceBreakdownOut,
    BalanceBreakdownPage,
    BalanceBreakdownSummaryOut,
    BalanceCategoryOut,
)
from app.schemas.common_schemas import Freshness
from app.services.freshness_interpreter import FreshnessInterpreter
from app.services.ownership import OwnershipScope

QUALIFIER_NOTICE = (
    "Information only. These rates and dates apply to this category as supplied by the source; "
    "they are not a pricing promise or an entitlement."
)


class BalanceService:
    def __init__(self, db: Session, scope: OwnershipScope) -> None:
        self.scope = scope
        self.accounts = AccountRepository(db)
        self.repo = BalanceRepository(db)
        self.freshness = FreshnessInterpreter(SettingsRepository(db))

    def list_for_account(self, account_id: uuid.UUID, limit: int, offset: int) -> BalanceBreakdownPage:
        account = self.accounts.get_for_customer(self.scope.customer_id, account_id)
        if account is None:
            raise NotFoundError("account not found for this customer")
        rows, total = self.repo.list_for_account(account.id, limit, offset)
        items = [
            BalanceBreakdownSummaryOut(
                id=r.id,
                account_id=r.account_id,
                source_ref=r.source_ref,
                as_of=r.as_of,
                total_outstanding=r.total_outstanding,
                pending_total=r.pending_total,
                is_zero_balance=r.is_zero_balance,
                freshness=self._freshness(r),
            )
            for r in rows
        ]
        return BalanceBreakdownPage(items=items, total=total, limit=limit, offset=offset)

    def get(self, breakdown_id: uuid.UUID) -> BalanceBreakdownOut:
        row = self.repo.get_for_customer(self.scope.customer_id, breakdown_id)
        if row is None:
            raise NotFoundError("balance breakdown not found for this customer")
        return BalanceBreakdownOut(
            id=row.id,
            account_id=row.account_id,
            source_ref=row.source_ref,
            as_of=row.as_of,
            total_outstanding=row.total_outstanding,
            pending_total=row.pending_total,
            is_zero_balance=row.is_zero_balance,
            purchases_subtotal=row.purchases_subtotal,
            balance_transfers_subtotal=row.balance_transfers_subtotal,
            categories=[self._category(c) for c in self.repo.categories(row.id)],
            freshness=self._freshness(row),
            notice=InformationOnlyPolicy.SNAPSHOT_NOTICE,
        )

    @staticmethod
    def _category(c: BalanceCategory) -> BalanceCategoryOut:
        out = BalanceCategoryOut.model_validate(c)
        if any(
            v is not None
            for v in (c.category_apr_percent, c.promo_end_date, c.revert_rate_percent, c.days_to_expiry)
        ):
            out.qualifier_notice = QUALIFIER_NOTICE
        return out

    def _freshness(self, row: BalanceBreakdown) -> Freshness:
        return self.freshness.for_kind("balance_breakdown", row.as_of)

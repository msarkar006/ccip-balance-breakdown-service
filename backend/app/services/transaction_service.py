"""Transaction list rules: source status and dates verbatim, freshness labelled, ownership enforced."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.setting_repository import SettingsRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction_schemas import TransactionOut, TransactionPage
from app.services.freshness_interpreter import FreshnessInterpreter
from app.services.ownership import OwnershipScope


class TransactionService:
    def __init__(self, db: Session, scope: OwnershipScope) -> None:
        self.scope = scope
        self.accounts = AccountRepository(db)
        self.repo = TransactionRepository(db)
        self.freshness = FreshnessInterpreter(SettingsRepository(db))

    def list_transactions(
        self, account_id: uuid.UUID, status: str | None, limit: int, offset: int
    ) -> TransactionPage:
        account = self.accounts.get_for_customer(self.scope.customer_id, account_id)
        if account is None:
            raise NotFoundError("account not found for this customer")
        rows, total = self.repo.list_for_account(account.id, status, limit, offset)
        items = [self._to_out(t, pan) for t, pan in rows]
        return TransactionPage(items=items, total=total, limit=limit, offset=offset)

    def get_transaction(self, transaction_id: uuid.UUID) -> TransactionOut:
        found = self.repo.get_for_customer(self.scope.customer_id, transaction_id)
        if found is None:
            raise NotFoundError("transaction not found for this customer")
        return self._to_out(*found)

    def _to_out(self, t: Transaction, pan: str | None) -> TransactionOut:
        return TransactionOut(
            id=t.id,
            account_id=t.account_id,
            card_id=t.card_id,
            masked_pan=pan,
            source_ref=t.source_ref,
            transaction_status=t.transaction_status,
            transaction_time=t.transaction_time,
            posted_date=t.posted_date,
            transaction_amount=t.transaction_amount,
            merchant_name=t.merchant_name,
            merchant_category_code=t.merchant_category_code,
            eligible_for_instalment=t.eligible_for_instalment,
            freshness=self.freshness.for_kind("transaction", t.transaction_time),
        )

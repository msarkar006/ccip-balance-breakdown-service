"""Account overview rules: fields copied verbatim, absent stay null, no freshness for account fields."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import Account
from app.policy import InformationOnlyPolicy
from app.repositories.account_repository import AccountRepository
from app.repositories.card_repository import CardRepository
from app.schemas.account_schemas import AccountOut, AccountPage
from app.schemas.card_schemas import CardOut, CardPage
from app.schemas.common_schemas import Freshness
from app.services.ownership import OwnershipScope

ACCOUNT_FRESHNESS = Freshness(state="freshness unavailable", basis="account fields carry no source timestamp")


def to_account_out(account: Account) -> AccountOut:
    return AccountOut(
        id=account.id,
        source_ref=account.source_ref,
        product_name=account.product_name,
        account_status=account.account_status,
        opened_on=account.opened_on,
        currency=account.currency,
        credit_limit=account.credit_limit,
        available_credit=account.available_credit,
        current_balance=account.current_balance,
        standard_purchase_apr=account.standard_purchase_apr,
        last_statement_balance=account.last_statement_balance,
        next_statement_date=account.next_statement_date,
        payment_due_date=account.payment_due_date,
        minimum_payment=account.minimum_payment,
        freshness=ACCOUNT_FRESHNESS,
        informational_notice=InformationOnlyPolicy.ACCOUNT_NOTICE,
    )


class AccountService:
    def __init__(self, db: Session, scope: OwnershipScope) -> None:
        self.repo = AccountRepository(db)
        self.cards = CardRepository(db)
        self.scope = scope

    def list_accounts(self, limit: int, offset: int) -> AccountPage:
        rows, total = self.repo.list_for_customer(self.scope.customer_id, limit, offset)
        return AccountPage(items=[to_account_out(r) for r in rows], total=total, limit=limit, offset=offset)

    def get_account(self, account_id: uuid.UUID) -> AccountOut:
        account = self.repo.get_for_customer(self.scope.customer_id, account_id)
        if account is None:
            raise NotFoundError("account not found for this customer")
        return to_account_out(account)

    def list_cards(self, account_id: uuid.UUID, limit: int, offset: int) -> CardPage:
        account = self.repo.get_for_customer(self.scope.customer_id, account_id)
        if account is None:
            raise NotFoundError("account not found for this customer")
        rows, total = self.cards.list_for_account(account.id, limit, offset)
        return CardPage(
            items=[CardOut.model_validate(r) for r in rows], total=total, limit=limit, offset=offset
        )

"""Payment history rules: source values verbatim, masked source account, informational notice per row."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import Payment
from app.policy import InformationOnlyPolicy
from app.repositories.account_repository import AccountRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.common_schemas import Freshness
from app.schemas.payment_schemas import PaymentOut, PaymentPage
from app.services.ownership import OwnershipScope


class PaymentService:
    def __init__(self, db: Session, scope: OwnershipScope) -> None:
        self.scope = scope
        self.accounts = AccountRepository(db)
        self.repo = PaymentRepository(db)

    def list_payments(
        self,
        account_id: uuid.UUID,
        payment_type: str | None,
        payment_status: str | None,
        limit: int,
        offset: int,
    ) -> PaymentPage:
        account = self.accounts.get_for_customer(self.scope.customer_id, account_id)
        if account is None:
            raise NotFoundError("account not found for this customer")
        rows, total = self.repo.list_for_account(account.id, payment_type, payment_status, limit, offset)
        return PaymentPage(items=[self._to_out(p) for p in rows], total=total, limit=limit, offset=offset)

    def get_payment(self, payment_id: uuid.UUID) -> PaymentOut:
        payment = self.repo.get_for_customer(self.scope.customer_id, payment_id)
        if payment is None:
            raise NotFoundError("payment not found for this customer")
        return self._to_out(payment)

    @staticmethod
    def _to_out(p: Payment) -> PaymentOut:
        return PaymentOut(
            id=p.id,
            account_id=p.account_id,
            source_ref=p.source_ref,
            via_mandate_ref=p.via_mandate_ref,
            payment_type=p.payment_type,
            payment_method=p.payment_method,
            payment_status=p.payment_status,
            payment_amount=p.payment_amount,
            payment_date=p.payment_date,
            source_bank_name=p.source_bank_name,
            source_masked_account=p.source_masked_account,
            # A payment carries only a calendar date, never a source timestamp.
            freshness=Freshness(state="freshness unavailable", basis="no source timestamp"),
            informational_notice=InformationOnlyPolicy.PAYMENT_NOTICE,
        )

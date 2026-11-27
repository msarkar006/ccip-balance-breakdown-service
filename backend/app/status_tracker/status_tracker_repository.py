"""
Status tracker repository - database access layer for tracking.
"""
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.balance_transfer import BalanceTransfer
from app.models.direct_debit_change_request import DirectDebitChangeRequest
from app.models.money_transfer import MoneyTransfer
from app.models.payment import Payment
from app.models.tracking_event import TrackingEvent

logger = get_logger(__name__)


class StatusTrackerRepository:
    """Repository for status tracker data access."""

    def __init__(self, db: Session):
        self.db = db

    def get_payments_by_account(
        self,
        account_id: int,
        status_filter: Optional[str] = None,
    ) -> list[Payment]:
        """Get payments for account with optional status filtering."""
        query = self.db.query(Payment).filter(Payment.account_id == account_id)

        if status_filter == "unresolved":
            # Unresolved: Submitted, Processing, Restricted, Failed
            query = query.filter(
                Payment.status.in_(["Submitted", "Processing", "Restricted", "Failed"])
            )

        return query.order_by(Payment.created_at.desc()).all()

    def get_money_transfers_by_account(
        self,
        account_id: int,
        status_filter: Optional[str] = None,
    ) -> list[MoneyTransfer]:
        """Get money transfers for account with optional status filtering."""
        query = self.db.query(MoneyTransfer).filter(MoneyTransfer.account_id == account_id)

        if status_filter == "unresolved":
            # Unresolved: Submitted, Processing, Blocked, Failed, Delayed
            query = query.filter(
                MoneyTransfer.status.in_(["Submitted", "Processing", "Blocked", "Failed", "Delayed", "Rejected"])
            )

        return query.order_by(MoneyTransfer.created_at.desc()).all()

    def get_balance_transfers_by_account(
        self,
        account_id: int,
        status_filter: Optional[str] = None,
    ) -> list[BalanceTransfer]:
        """Get balance transfers for account with optional status filtering."""
        query = self.db.query(BalanceTransfer).filter(BalanceTransfer.account_id == account_id)

        if status_filter == "unresolved":
            # Unresolved: Submitted, ReviewRequired, Processing, Rejected
            query = query.filter(
                BalanceTransfer.status.in_(["Submitted", "ReviewRequired", "Processing", "Rejected"])
            )

        return query.order_by(BalanceTransfer.created_at.desc()).all()

    def get_direct_debit_change_requests_by_account(
        self,
        account_id: int,
        status_filter: Optional[str] = None,
    ) -> list[DirectDebitChangeRequest]:
        """Get direct debit change requests for account with optional status filtering."""
        from app.models.direct_debit_mandate import DirectDebitMandate

        # Join through mandate to get account_id
        query = self.db.query(DirectDebitChangeRequest).join(
            DirectDebitMandate,
            DirectDebitChangeRequest.mandate_id == DirectDebitMandate.id
        ).filter(
            DirectDebitMandate.account_id == account_id
        )

        if status_filter == "unresolved":
            # Unresolved: Submitted, Processing, ReviewRequired, Rejected
            query = query.filter(
                DirectDebitChangeRequest.status.in_(["Submitted", "Processing", "ReviewRequired", "Rejected"])
            )

        return query.order_by(DirectDebitChangeRequest.created_at.desc()).all()

    def get_tracking_events_for_entity(
        self,
        entity_type: str,
        entity_id: str,
    ) -> list[TrackingEvent]:
        """Get tracking events for a specific entity."""
        return (
            self.db.query(TrackingEvent)
            .filter(
                and_(
                    TrackingEvent.entity_type == entity_type,
                    TrackingEvent.entity_id == entity_id,
                )
            )
            .order_by(TrackingEvent.occurred_at.asc())
            .all()
        )

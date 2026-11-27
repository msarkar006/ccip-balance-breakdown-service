"""
Payment repository - data access for payment history.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.tracking_event import TrackingEvent
from app.payments.payments_models import Payment


class PaymentsRepository:
    """Repository for payment data access."""

    def __init__(self, db: Session):
        self.db = db

    def get_payments_by_account(
        self,
        account_id: int,
        payment_type: Optional[str] = None,
        limit: int = 25,
        offset: int = 0
    ) -> tuple[list[Payment], int]:
        """
        Get payments for account ordered by scheduled_date/created_at DESC.

        Args:
            account_id: Account ID to filter by
            payment_type: Optional payment type filter (Scheduled, OneOff, DirectDebitCollection)
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            (payments, total_count)
        """
        # Build base query
        base_query = select(Payment).where(Payment.account_id == account_id)

        # Apply payment_type filter if provided (stub - stored but not in model yet)
        # For now we just filter by account_id

        # Get total count
        count_stmt = select(func.count(Payment.id)).where(Payment.account_id == account_id)
        total = self.db.execute(count_stmt).scalar_one()

        # Get paginated payments ordered by scheduled_date DESC NULLS LAST, then created_at DESC
        stmt = (
            base_query
            .order_by(Payment.scheduled_date.desc().nulls_last(), Payment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        payments = list(self.db.execute(stmt).scalars().all())

        return payments, total

    def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID."""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_tracking_events_for_payment(self, payment_id: int) -> list[TrackingEvent]:
        """
        Get tracking events for a payment ordered by occurred_at ASC.

        Args:
            payment_id: Payment ID

        Returns:
            List of tracking events ordered by occurred_at ASC
        """
        stmt = (
            select(TrackingEvent)
            .where(
                TrackingEvent.entity_type == "Payment",
                TrackingEvent.entity_id == str(payment_id)
            )
            .order_by(TrackingEvent.occurred_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_payment_by_idempotency(
        self, account_id: int, idempotency_key: str
    ) -> Optional[Payment]:
        """
        Find existing payment by idempotency key.

        Args:
            account_id: Account ID
            idempotency_key: Idempotency key

        Returns:
            Payment or None
        """
        return self.db.query(Payment).filter(
            Payment.account_id == account_id,
            Payment.idempotency_key == idempotency_key
        ).first()

    def create_payment(self, payment: Payment) -> Payment:
        """
        Create a new payment.

        Args:
            payment: Payment instance to persist

        Returns:
            Persisted Payment
        """
        self.db.add(payment)
        self.db.flush()
        return payment

    def create_tracking_event(self, event: TrackingEvent) -> TrackingEvent:
        """
        Create a tracking event.

        Args:
            event: TrackingEvent instance to persist

        Returns:
            Persisted TrackingEvent
        """
        self.db.add(event)
        self.db.flush()
        return event

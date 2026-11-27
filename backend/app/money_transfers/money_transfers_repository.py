"""
Money transfer repository - data access for money transfer tracking.
"""
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.money_transfer import MoneyTransfer
from app.models.payee import Payee
from app.models.tracking_event import TrackingEvent


class MoneyTransfersRepository:
    """Repository for money transfer data access."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_account(
        self,
        account_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[list[MoneyTransfer], int]:
        """
        Get paginated money transfers for an account.

        Args:
            account_id: Account ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of MoneyTransfer, total count)
        """
        query = self.db.query(MoneyTransfer).filter(
            MoneyTransfer.account_id == account_id
        )

        total = query.count()

        transfers = query.order_by(
            desc(MoneyTransfer.created_at)  # type: ignore
        ).limit(limit).offset(offset).all()

        return transfers, total

    def get_by_id(self, transfer_id: int) -> Optional[MoneyTransfer]:
        """
        Get money transfer by ID.

        Args:
            transfer_id: Money transfer ID

        Returns:
            MoneyTransfer if found, None otherwise
        """
        return self.db.query(MoneyTransfer).filter(
            MoneyTransfer.id == transfer_id
        ).first()

    def get_payee(self, payee_id: int) -> Optional[Payee]:
        """
        Get payee by ID.

        Args:
            payee_id: Payee ID

        Returns:
            Payee if found, None otherwise
        """
        return self.db.query(Payee).filter(
            Payee.id == payee_id
        ).first()

    def get_tracking_events(self, transfer_id: int) -> list[TrackingEvent]:
        """
        Get tracking events for a money transfer.

        Args:
            transfer_id: Money transfer ID

        Returns:
            List of TrackingEvent ordered by occurred_at ASC
        """
        return self.db.query(TrackingEvent).filter(
            TrackingEvent.entity_type == "MoneyTransfer",
            TrackingEvent.entity_id == str(transfer_id)
        ).order_by(TrackingEvent.occurred_at).all()

    def get_payees_by_account(
        self,
        account_id: int,
        limit: int = 25,
        offset: int = 0
    ) -> tuple[list[Payee], int]:
        """
        Get paginated payees for an account.

        Args:
            account_id: Account ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of Payee, total count)
        """
        query = self.db.query(Payee).filter(
            Payee.account_id == account_id,
            Payee.is_active == True
        )

        total = query.count()

        payees = query.order_by(
            desc(Payee.created_at)  # type: ignore
        ).limit(limit).offset(offset).all()

        return payees, total

    def get_by_idempotency_key(
        self,
        account_id: int,
        idempotency_key: str
    ) -> Optional[MoneyTransfer]:
        """
        Find money transfer by idempotency key.

        Args:
            account_id: Account ID
            idempotency_key: Idempotency key

        Returns:
            MoneyTransfer if found, None otherwise
        """
        return self.db.query(MoneyTransfer).filter(
            MoneyTransfer.account_id == account_id,
            MoneyTransfer.idempotency_key == idempotency_key
        ).first()

    def create(self, transfer: MoneyTransfer) -> MoneyTransfer:
        """
        Create a new money transfer.

        Args:
            transfer: MoneyTransfer instance

        Returns:
            Created MoneyTransfer with assigned ID
        """
        self.db.add(transfer)
        self.db.flush()
        return transfer

"""
Balance transfer repository - data access for balance transfer tracking.
"""
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.balance_transfers.balance_transfers_models import BalanceTransfer
from app.models.tracking_event import TrackingEvent


class BalanceTransfersRepository:
    """Repository for balance transfer data access."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_account(
        self,
        account_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[list[BalanceTransfer], int]:
        """
        Get paginated balance transfers for an account.

        Args:
            account_id: Account ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of BalanceTransfer, total count)
        """
        query = self.db.query(BalanceTransfer).filter(
            BalanceTransfer.account_id == account_id
        )

        total = query.count()

        transfers = query.order_by(
            desc(BalanceTransfer.created_at)  # type: ignore
        ).limit(limit).offset(offset).all()

        return transfers, total

    def get_by_id(self, transfer_id: int) -> Optional[BalanceTransfer]:
        """
        Get balance transfer by ID.

        Args:
            transfer_id: Balance transfer ID

        Returns:
            BalanceTransfer if found, None otherwise
        """
        return self.db.query(BalanceTransfer).filter(
            BalanceTransfer.id == transfer_id
        ).first()

    def get_tracking_events(self, transfer_id: int) -> list[TrackingEvent]:
        """
        Get tracking events for a balance transfer.

        Args:
            transfer_id: Balance transfer ID

        Returns:
            List of TrackingEvent ordered by occurred_at ASC
        """
        return self.db.query(TrackingEvent).filter(
            TrackingEvent.entity_type == "BalanceTransfer",
            TrackingEvent.entity_id == str(transfer_id)
        ).order_by(TrackingEvent.occurred_at).all()

    def get_by_idempotency_key(
        self,
        account_id: int,
        idempotency_key: str
    ) -> Optional[BalanceTransfer]:
        """
        Find balance transfer by idempotency key.

        Args:
            account_id: Account ID
            idempotency_key: Idempotency key

        Returns:
            BalanceTransfer if found, None otherwise
        """
        return self.db.query(BalanceTransfer).filter(
            BalanceTransfer.account_id == account_id,
            BalanceTransfer.idempotency_key == idempotency_key
        ).first()

    def create(self, transfer: BalanceTransfer) -> BalanceTransfer:
        """
        Create a new balance transfer.

        Args:
            transfer: BalanceTransfer instance

        Returns:
            Created BalanceTransfer with assigned ID
        """
        self.db.add(transfer)
        self.db.flush()
        return transfer

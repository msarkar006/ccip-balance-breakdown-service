"""
Transaction service - business logic for transaction history.
"""
from sqlalchemy.orm import Session

from app.sync.sync_service import FreshnessAndSyncService
from app.transactions.transactions_repository import TransactionsRepository
from app.transactions.transactions_schemas import TransactionListResponse, TransactionResponse


class TransactionService:
    """Transaction service for transaction history retrieval."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = TransactionsRepository(db)
        self.freshness_service = FreshnessAndSyncService()

    def get_transactions(
        self,
        account_id: int,
        limit: int = 25,
        offset: int = 0
    ) -> TransactionListResponse:
        """
        Get paginated transaction history ordered by transaction_date DESC.

        Args:
            account_id: Account ID to filter by
            limit: Maximum items to return (1-100, default 25)
            offset: Number of items to skip

        Returns:
            TransactionListResponse with page envelope
        """
        # Validate pagination parameters
        limit = max(1, min(100, limit))
        offset = max(0, offset)

        # Get transactions and total count
        transactions, total = self.repository.get_transactions_by_account(
            account_id=account_id,
            limit=limit,
            offset=offset
        )

        # Convert to response models
        items = [TransactionResponse.model_validate(txn) for txn in transactions]

        # Compute has_more flag
        has_more = (offset + limit) < total

        # Empty state message
        empty_state_message = "No transactions found for this account" if total == 0 else None

        # Get freshness (stub returns "Current")
        freshness_info = self.freshness_service.get_freshness()
        freshness = {
            "level": freshness_info.level,
            "as_of": freshness_info.as_of
        }

        return TransactionListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
            empty_state_message=empty_state_message,
            freshness=freshness
        )

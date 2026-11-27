"""
Transaction repository - data access for transaction history.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.transactions.transactions_models import Transaction


class TransactionsRepository:
    """Repository for transaction data access."""

    def __init__(self, db: Session):
        self.db = db

    def get_transactions_by_account(
        self,
        account_id: int,
        limit: int = 25,
        offset: int = 0
    ) -> tuple[list[Transaction], int]:
        """
        Get transactions for account ordered by transaction_date DESC.

        Returns:
            (transactions, total_count)
        """
        # Get total count
        count_stmt = select(func.count(Transaction.id)).where(
            Transaction.account_id == account_id
        )
        total = self.db.execute(count_stmt).scalar_one()

        # Get paginated transactions ordered by transaction_date DESC
        stmt = (
            select(Transaction)
            .where(Transaction.account_id == account_id)
            .order_by(Transaction.transaction_date.desc())
            .limit(limit)
            .offset(offset)
        )
        transactions = list(self.db.execute(stmt).scalars().all())

        return transactions, total

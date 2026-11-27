"""
Balance breakdown repository for data access.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.balance_breakdown import BalanceBreakdown
from app.models.balance_category import BalanceCategory

logger = get_logger(__name__)


class BalanceBreakdownsRepository:
    """Repository for balance breakdown data access."""

    def __init__(self, db: Session):
        self.db = db

    def get_current_by_account(self, account_id: int) -> Optional[BalanceBreakdown]:
        """
        Get the most recent balance breakdown for an account.

        Args:
            account_id: Account ID

        Returns:
            Most recent BalanceBreakdown or None
        """
        stmt = (
            select(BalanceBreakdown)
            .where(BalanceBreakdown.account_id == account_id)
            .order_by(BalanceBreakdown.snapshot_date.desc())
            .limit(1)
        )
        result = self.db.execute(stmt).scalar_one_or_none()
        logger.info(f"Retrieved current balance breakdown for account {account_id}: {result.id if result else None}")
        return result

    def get_breakdown_by_id(self, breakdown_id: int) -> Optional[BalanceBreakdown]:
        """
        Get a balance breakdown by ID.

        Args:
            breakdown_id: Breakdown ID

        Returns:
            BalanceBreakdown or None
        """
        stmt = select(BalanceBreakdown).where(BalanceBreakdown.id == breakdown_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_categories_by_breakdown(self, breakdown_id: int) -> list[BalanceCategory]:
        """
        Get all categories for a breakdown, ordered by display_rank.

        Args:
            breakdown_id: Breakdown ID

        Returns:
            List of BalanceCategory ordered by display_rank
        """
        stmt = (
            select(BalanceCategory)
            .where(BalanceCategory.breakdown_id == breakdown_id)
            .order_by(BalanceCategory.display_rank.asc().nulls_last(), BalanceCategory.id.asc())
        )
        result = self.db.execute(stmt).scalars().all()
        logger.info(f"Retrieved {len(result)} categories for breakdown {breakdown_id}")
        return list(result)

    def get_category_by_id(self, breakdown_id: int, category_id: int) -> Optional[BalanceCategory]:
        """
        Get a specific category by breakdown and category IDs.

        Args:
            breakdown_id: Breakdown ID
            category_id: Category ID

        Returns:
            BalanceCategory or None
        """
        stmt = (
            select(BalanceCategory)
            .where(
                BalanceCategory.breakdown_id == breakdown_id,
                BalanceCategory.id == category_id
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

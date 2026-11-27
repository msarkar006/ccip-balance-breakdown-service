"""
Rewards, offers, and instalments repository - database access layer.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.balance_category import BalanceCategory
from app.models.instalment_plan import InstalmentPlan
from app.models.offer import Offer
from app.models.transaction import Transaction

logger = get_logger(__name__)


class RewardsOffersInstalmentsRepository:
    """Repository for rewards, offers, and instalments data access."""

    def __init__(self, db: Session):
        self.db = db

    def get_offers_by_account(
        self,
        account_id: int,
        context: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Offer], int]:
        """
        Get offers for an account with optional context filtering.

        Args:
            account_id: Account ID
            context: Optional context filter (BalanceTransfer, Rewards, Instalment, rewards_and_offers)
            limit: Maximum results per page
            offset: Pagination offset

        Returns:
            Tuple of (offer list, total count)
        """
        query = self.db.query(Offer).filter(
            Offer.account_id == account_id,
            Offer.status.in_(["Available", "Active"])
        )

        # Apply context filtering
        if context == "BalanceTransfer":
            query = query.filter(Offer.offer_type == "BalanceTransfer")
        elif context == "Rewards" or context == "rewards_and_offers":
            query = query.filter(Offer.offer_type == "Rewards")
        elif context == "Instalment":
            query = query.filter(Offer.offer_type == "Instalment")

        total = query.count()
        offers = query.order_by(Offer.valid_from.desc()).limit(limit).offset(offset).all()

        return offers, total

    def get_offer_by_id(self, offer_id: int) -> Optional[Offer]:
        """
        Get offer by ID.

        Args:
            offer_id: Offer ID

        Returns:
            Offer or None if not found
        """
        return self.db.query(Offer).filter(Offer.id == offer_id).first()

    def get_instalment_plans_by_account(
        self,
        account_id: int,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[InstalmentPlan], int]:
        """
        Get instalment plans for an account with optional status filtering.

        Args:
            account_id: Account ID
            status: Optional status filter (Active, Completed, Cancelled)
            limit: Maximum results per page
            offset: Pagination offset

        Returns:
            Tuple of (instalment plan list, total count)
        """
        query = self.db.query(InstalmentPlan).filter(
            InstalmentPlan.account_id == account_id
        )

        if status:
            query = query.filter(InstalmentPlan.status == status)

        total = query.count()
        plans = query.order_by(InstalmentPlan.created_at.desc()).limit(limit).offset(offset).all()

        return plans, total

    def get_instalment_plan_by_id(self, plan_id: int) -> Optional[InstalmentPlan]:
        """
        Get instalment plan by ID.

        Args:
            plan_id: Instalment plan ID

        Returns:
            InstalmentPlan or None if not found
        """
        return self.db.query(InstalmentPlan).filter(InstalmentPlan.id == plan_id).first()

    def get_source_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """
        Get source transaction for instalment plan.

        Args:
            transaction_id: Transaction ID

        Returns:
            Transaction or None if not found
        """
        return self.db.query(Transaction).filter(Transaction.id == transaction_id).first()

    def get_linked_balance_category(self, instalment_plan_id: int) -> Optional[BalanceCategory]:
        """
        Get linked balance category for instalment plan.

        Args:
            instalment_plan_id: Instalment plan ID

        Returns:
            BalanceCategory or None if not found
        """
        return self.db.query(BalanceCategory).filter(
            BalanceCategory.source_instalment_plan_id == instalment_plan_id
        ).first()

"""
Rewards, offers, and instalments service with business logic.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.rewards_offers_instalments.rewards_offers_instalments_repository import (
    RewardsOffersInstalmentsRepository,
)
from app.rewards_offers_instalments.rewards_offers_instalments_schemas import (
    BalanceEffect,
    InstalmentPlanDetailResponse,
    InstalmentPlanListItem,
    InstalmentPlanListResponse,
    LinkedBalanceCategory,
    OfferDetailResponse,
    OfferListItem,
    OfferListResponse,
)

logger = get_logger(__name__)


class RewardsOffersInstalmentsService:
    """Service for rewards, offers, and instalments operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = RewardsOffersInstalmentsRepository(db)

    def list_offers(
        self,
        account_id: int,
        context: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> OfferListResponse:
        """
        List offers for an account with optional context filtering.

        Args:
            account_id: Account ID
            context: Optional context filter
            limit: Maximum results per page
            offset: Pagination offset

        Returns:
            OfferListResponse with paginated offers
        """
        offers, total = self.repository.get_offers_by_account(
            account_id=account_id,
            context=context,
            limit=limit,
            offset=offset,
        )

        items = [
            OfferListItem(
                id=offer.id,
                offer_code=offer.offer_code,
                offer_title=offer.offer_title,
                offer_description=offer.offer_description,
                offer_type=offer.offer_type,
                status=offer.status,
                valid_from=offer.valid_from,
                valid_until=offer.valid_until,
            )
            for offer in offers
        ]

        has_more = (offset + limit) < total

        return OfferListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )

    def get_offer_detail(self, offer_id: int) -> OfferDetailResponse:
        """
        Get detailed information for a specific offer.

        Args:
            offer_id: Offer ID

        Returns:
            OfferDetailResponse with full context

        Raises:
            NotFoundError: If offer not found
        """
        offer = self.repository.get_offer_by_id(offer_id)
        if not offer:
            logger.warning(f"Offer {offer_id} not found")
            raise NotFoundError("Offer not found")

        return OfferDetailResponse(
            id=offer.id,
            account_id=offer.account_id,
            offer_code=offer.offer_code,
            offer_title=offer.offer_title,
            offer_description=offer.offer_description,
            offer_type=offer.offer_type,
            status=offer.status,
            valid_from=offer.valid_from,
            valid_until=offer.valid_until,
            created_at=offer.created_at,
            updated_at=offer.updated_at,
        )

    def get_rewards_summary(self, account_id: int) -> dict:
        """
        Get rewards programme summary with servicing-relevant offers.

        Args:
            account_id: Account ID

        Returns:
            Dict with programme (null when absent) and relevant_offers array
        """
        from datetime import datetime

        from app.models.rewards_programme import RewardsProgramme

        # Query rewards programme
        programme = self.db.query(RewardsProgramme).filter(
            RewardsProgramme.account_id == account_id
        ).first()

        programme_data = None
        if programme:
            programme_data = {
                "programme_name": programme.programme_name,
                "points_balance": programme.points_balance,
                "status": programme.status,
                "as_of": datetime.utcnow(),
            }

        # Query servicing-relevant offers (context=rewards_and_offers)
        relevant_offers, _ = self.repository.get_offers_by_account(
            account_id=account_id,
            context="rewards_and_offers",
            limit=100,
            offset=0
        )

        relevant_offers_data = [
            {
                "id": offer.id,
                "offer_code": offer.offer_code,
                "offer_title": offer.offer_title,
                "offer_type": offer.offer_type,
                "status": offer.status,
            }
            for offer in relevant_offers
        ]

        return {
            "programme": programme_data,
            "relevant_offers": relevant_offers_data,
            "freshness": {
                "level": "Current",
                "as_of": datetime.utcnow(),
            }
        }

    def list_instalment_plans(
        self,
        account_id: int,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> InstalmentPlanListResponse:
        """
        List instalment plans for an account with optional status filtering.

        Args:
            account_id: Account ID
            status: Optional status filter (defaults to "Active")
            limit: Maximum results per page
            offset: Pagination offset

        Returns:
            InstalmentPlanListResponse with paginated plans
        """
        # Default to Active status if not specified
        if status is None:
            status = "Active"

        plans, total = self.repository.get_instalment_plans_by_account(
            account_id=account_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        items = [
            InstalmentPlanListItem(
                id=plan.id,
                plan_reference=plan.plan_reference,
                plan_name=f"{plan.plan_reference} - {plan.instalment_count} months",
                original_amount=plan.original_amount,
                remaining_balance=plan.remaining_balance,
                instalment_count=plan.instalment_count,
                monthly_payment=plan.monthly_payment,
                apr=plan.apr,
                status=plan.status,
                created_at=plan.created_at,
            )
            for plan in plans
        ]

        has_more = (offset + limit) < total
        empty_state_message = "No active instalment plans found" if total == 0 else None

        return InstalmentPlanListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
            empty_state_message=empty_state_message,
        )

    def get_instalment_plan_detail(self, plan_id: int) -> InstalmentPlanDetailResponse:
        """
        Get detailed information for a specific instalment plan.

        Args:
            plan_id: Instalment plan ID

        Returns:
            InstalmentPlanDetailResponse with full context

        Raises:
            NotFoundError: If plan not found
        """
        plan = self.repository.get_instalment_plan_by_id(plan_id)
        if not plan:
            logger.warning(f"Instalment plan {plan_id} not found")
            raise NotFoundError("Instalment plan not found")

        # Get source transaction if available (from seed or external data)
        source_transaction = None
        # Note: source_transaction_id would be on the plan if it existed
        # For now, this is None as per the requirement (FR-INS-002 deferred)

        # Get linked balance category
        linked_category_obj = self.repository.get_linked_balance_category(plan.id)
        linked_category = None
        if linked_category_obj:
            linked_category = LinkedBalanceCategory(
                category_id=linked_category_obj.id,
                category_name=linked_category_obj.category_name,
                category_amount=linked_category_obj.category_amount,
            )

        # Build balance effect explanation
        is_reflected = linked_category is not None
        if is_reflected:
            explanation = (
                f"The remaining balance of £{plan.remaining_balance:.2f} is included in your "
                f"total balance under the '{linked_category.category_name}' category. "
                f"Monthly instalments of £{plan.monthly_payment:.2f} reduce this amount."
            )
        else:
            explanation = (
                f"This instalment plan has a remaining balance of £{plan.remaining_balance:.2f}. "
                "It may not yet be reflected in your current balance breakdown."
            )

        balance_effect = BalanceEffect(
            is_reflected_in_balance=is_reflected,
            explanation=explanation,
        )

        return InstalmentPlanDetailResponse(
            id=plan.id,
            account_id=plan.account_id,
            plan_reference=plan.plan_reference,
            plan_name=f"{plan.plan_reference} - {plan.instalment_count} months",
            original_amount=plan.original_amount,
            remaining_balance=plan.remaining_balance,
            instalment_count=plan.instalment_count,
            monthly_payment=plan.monthly_payment,
            apr=plan.apr,
            status=plan.status,
            source_transaction=source_transaction,
            linked_category=linked_category,
            balance_effect=balance_effect,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

"""
Balance breakdown service with business logic.
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.balance_breakdowns.balance_breakdowns_repository import BalanceBreakdownsRepository
from app.balance_breakdowns.balance_breakdowns_schemas import (
    BalanceBreakdownResponse,
    BalanceCategoryItem,
    CategoryDetailResponse,
    FreshnessInfo,
    SourceLink,
)
from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.sync.sync_service import FreshnessAndSyncService

logger = get_logger(__name__)


class BalanceBreakdownService:
    """Service for balance breakdown operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = BalanceBreakdownsRepository(db)
        self.freshness_service = FreshnessAndSyncService()

    def get_current_breakdown(self, account_id: int) -> BalanceBreakdownResponse:
        """
        Get the current balance breakdown for an account.

        Args:
            account_id: Account ID

        Returns:
            BalanceBreakdownResponse with categories and freshness

        Raises:
            NotFoundError: If no breakdown exists for the account
        """
        # Get breakdown
        breakdown = self.repository.get_current_by_account(account_id)
        if not breakdown:
            logger.warning(f"No balance breakdown found for account {account_id}")
            raise NotFoundError(f"No balance breakdown found for account {account_id}")

        # Get categories ordered by display_rank
        categories = self.repository.get_categories_by_breakdown(breakdown.id)

        # Compute pending_total by summing pending transactions
        from app.models.transaction import Transaction
        pending_total = self.db.query(
            func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))
        ).filter(
            Transaction.account_id == account_id,
            Transaction.status == "Pending"
        ).scalar() or Decimal("0.00")

        # Get freshness
        freshness_level = self.freshness_service.classify("balance_breakdown", breakdown.id)
        as_of = self.freshness_service.get_as_of_timestamp("balance_breakdown", breakdown.id)

        # Build category items with source linkage
        category_items = []
        for cat in categories:
            source_link = self._build_source_link(cat)
            category_items.append(
                BalanceCategoryItem(
                    id=cat.id,
                    category_name=cat.category_name,
                    category_amount=cat.category_amount,
                    apr=cat.apr,
                    display_rank=cat.display_rank,
                    promo_rate=cat.promo_rate,
                    promo_end_date=cat.promo_end_date,
                    source_link=source_link,
                )
            )

        return BalanceBreakdownResponse(
            id=breakdown.id,
            account_id=breakdown.account_id,
            total_balance=breakdown.total_balance,
            pending_total=pending_total,
            snapshot_date=breakdown.snapshot_date,
            categories=category_items,
            freshness=FreshnessInfo(level=freshness_level, as_of=as_of),
            created_at=breakdown.created_at,
            updated_at=breakdown.updated_at,
        )

    def get_category_detail(self, breakdown_id: int, category_id: int) -> CategoryDetailResponse:
        """
        Get detailed information for a specific category.

        Args:
            breakdown_id: Breakdown ID
            category_id: Category ID

        Returns:
            CategoryDetailResponse with full context

        Raises:
            NotFoundError: If category not found
        """
        category = self.repository.get_category_by_id(breakdown_id, category_id)
        if not category:
            logger.warning(f"Category {category_id} not found in breakdown {breakdown_id}")
            raise NotFoundError("Category not found")

        source_link = self._build_source_link(category)

        return CategoryDetailResponse(
            id=category.id,
            breakdown_id=category.breakdown_id,
            category_name=category.category_name,
            category_amount=category.category_amount,
            apr=category.apr,
            display_rank=category.display_rank,
            promo_rate=category.promo_rate,
            promo_end_date=category.promo_end_date,
            source_link=source_link,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )

    def _build_source_link(self, category) -> Optional[SourceLink]:
        """
        Build source link object if category has source linkage.

        Args:
            category: BalanceCategory instance

        Returns:
            SourceLink or None
        """
        if category.source_balance_transfer_id:
            # Fetch the transfer reference if needed
            from app.models.balance_transfer import BalanceTransfer
            transfer = self.db.query(BalanceTransfer).filter(
                BalanceTransfer.id == category.source_balance_transfer_id
            ).first()
            return SourceLink(
                source_type="BalanceTransfer",
                source_id=category.source_balance_transfer_id,
                source_reference=transfer.external_transfer_id if transfer else None,
            )
        elif category.source_instalment_plan_id:
            # Fetch the plan reference if needed
            from app.models.instalment_plan import InstalmentPlan
            plan = self.db.query(InstalmentPlan).filter(
                InstalmentPlan.id == category.source_instalment_plan_id
            ).first()
            return SourceLink(
                source_type="InstalmentPlan",
                source_id=category.source_instalment_plan_id,
                source_reference=plan.plan_reference if plan else None,
            )
        return None

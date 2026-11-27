"""
Rewards, offers, and instalments API router.
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.app_user import AppUser
from app.rewards_offers_instalments.rewards_offers_instalments_schemas import (
    InstalmentPlanDetailResponse,
    InstalmentPlanListResponse,
    OfferListResponse,
)
from app.rewards_offers_instalments.rewards_offers_instalments_service import (
    RewardsOffersInstalmentsService,
)

router = APIRouter(prefix="/api/v1/offers", tags=["offers"])
rewards_router = APIRouter(prefix="/api/v1/rewards", tags=["rewards"])
instalments_router = APIRouter(prefix="/api/v1/instalments", tags=["instalments"])


@router.get("", response_model=OfferListResponse)
def list_offers(
    account_id: int = Query(..., description="Account ID to retrieve offers for"),
    context: Optional[str] = Query(None, description="Offer context filter: BalanceTransfer, Rewards, Instalment"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    List offers for an account with optional filtering.

    Returns paginated list of offers filtered by:
    - Account ID (required)
    - Context (optional): BalanceTransfer, Rewards, Instalment
    - Status: Only Available or Active offers

    Response includes pagination metadata with has_more flag.
    """
    service = RewardsOffersInstalmentsService(db)
    return service.list_offers(
        account_id=account_id,
        context=context,
        limit=limit,
        offset=offset,
    )


@rewards_router.get("")
def get_rewards_summary(
    account_id: int = Query(..., description="Account ID to retrieve rewards for"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get rewards programme summary with servicing-relevant offers.

    Returns:
        - programme: Rewards programme object (null when absent)
        - relevant_offers: Array of servicing-relevant offers filtered by context=rewards_and_offers
        - freshness: Freshness object

    Empty state: programme: null, relevant_offers: []
    """
    service = RewardsOffersInstalmentsService(db)
    return service.get_rewards_summary(account_id=account_id)


@instalments_router.get("", response_model=InstalmentPlanListResponse)
def list_instalment_plans(
    account_id: int = Query(..., description="Account ID to retrieve instalment plans for"),
    status: Optional[str] = Query("Active", description="Status filter: Active, Completed, Cancelled"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    List instalment plans for an account.

    Returns paginated list of instalment plans filtered by:
    - Account ID (required)
    - Status (defaults to Active): Active, Completed, Cancelled

    Response includes:
    - Paginated plan history ordered by start_date DESC
    - Plan obligation context (original amount, remaining balance, monthly payment)
    - empty_state_message when no plans found
    """
    service = RewardsOffersInstalmentsService(db)
    return service.list_instalment_plans(
        account_id=account_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@instalments_router.get("/{plan_id}", response_model=InstalmentPlanDetailResponse)
def get_instalment_plan_detail(
    plan_id: int = Path(..., description="Instalment plan ID"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Get detailed information for a specific instalment plan.

    Returns:
        - Plan resource with obligation details
        - source_transaction object when sourced from transaction (FR-INS-002 deferred, returns None)
        - linked_category: Balance category linked via source_instalment_plan_id
        - balance_effect: Explanation of how plan affects balance
            - is_reflected_in_balance: true when linked category exists
            - explanation: Text explaining relationship to total balance
    """
    service = RewardsOffersInstalmentsService(db)
    return service.get_instalment_plan_detail(plan_id=plan_id)

"""
Balance breakdown API router.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.balance_breakdowns.balance_breakdowns_schemas import (
    BalanceBreakdownResponse,
    CategoryDetailResponse,
)
from app.balance_breakdowns.balance_breakdowns_service import BalanceBreakdownService
from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.app_user import AppUser

router = APIRouter(prefix="/api/v1/balance-breakdowns", tags=["balance-breakdowns"])


@router.get("/current", response_model=BalanceBreakdownResponse)
def get_current_balance_breakdown(
    account_id: int = Query(..., description="Account ID to retrieve breakdown for"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Get the current balance breakdown for an account.

    Returns the most recent balance breakdown snapshot with:
    - Total balance and pending amounts
    - Ordered list of balance categories
    - Freshness disclosure
    - Source linkage for categories tied to transfers or instalments
    """
    service = BalanceBreakdownService(db)
    return service.get_current_breakdown(account_id)


@router.get("/{breakdown_id}/categories/{category_id}", response_model=CategoryDetailResponse)
def get_category_detail(
    breakdown_id: int,
    category_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Get detailed information for a specific balance category.

    Provides:
    - Full category context including APR, promo details
    - Source linkage if category is tied to a transfer or instalment
    """
    service = BalanceBreakdownService(db)
    return service.get_category_detail(breakdown_id, category_id)

"""
Transaction router - API endpoints for transaction history.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.app_user import AppUser
from app.transactions.transactions_schemas import TransactionListResponse
from app.transactions.transactions_service import TransactionService

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("", response_model=TransactionListResponse)
def get_transactions(
    account_id: int = Query(..., description="Account ID to filter transactions"),
    limit: int = Query(25, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user)
):
    """
    Get paginated transaction history for an account.

    Transactions are ordered by transaction_date DESC with pending and posted distinction.
    """
    service = TransactionService(db)
    return service.get_transactions(
        account_id=account_id,
        limit=limit,
        offset=offset
    )

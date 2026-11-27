"""
Accounts domain router - API endpoints for account operations.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.accounts.accounts_schemas import (
    AccountListResponse,
    AccountOverviewResponse,
    AccountSelectionRequest,
    AccountSelectionResponse,
)
from app.accounts.accounts_service import AccountOverviewService
from app.auth.auth_models import AppUser, UserSession
from app.core.database import get_db
from app.middleware.auth import get_current_user, get_current_user_session

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


# Note: For this demo, we're using a stub customer_id of 1
# In a real implementation, this would be retrieved from the authenticated user context
STUB_CUSTOMER_ID = 1


@router.get("", response_model=AccountListResponse, status_code=status.HTTP_200_OK)
def list_accounts(
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AccountListResponse:
    """
    List all accounts for the current customer.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        List of accounts
    """
    service = AccountOverviewService(db)
    return service.list_accounts(STUB_CUSTOMER_ID)


@router.get("/{account_id}/overview", response_model=AccountOverviewResponse, status_code=status.HTTP_200_OK)
def get_account_overview(
    account_id: int,
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AccountOverviewResponse:
    """
    Get detailed overview for a specific account.

    Args:
        account_id: Account ID
        user: Current authenticated user
        db: Database session

    Returns:
        Detailed account overview
    """
    service = AccountOverviewService(db)
    return service.get_account_overview(account_id, STUB_CUSTOMER_ID, user)


@router.put("/selection", response_model=AccountSelectionResponse, status_code=status.HTTP_200_OK)
def select_account(
    request: AccountSelectionRequest,
    user_session: tuple[AppUser, UserSession] = Depends(get_current_user_session),
    db: Session = Depends(get_db)
) -> AccountSelectionResponse:
    """
    Select an account for the current session context.

    Args:
        request: Account selection request
        user_session: Current authenticated user and session
        db: Database session

    Returns:
        Account selection response
    """
    user, session = user_session
    service = AccountOverviewService(db)
    return service.select_account(session.id, request.account_id, STUB_CUSTOMER_ID, user)

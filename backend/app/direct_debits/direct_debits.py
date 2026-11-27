"""
Direct debit router - API endpoints for direct debit management.
"""
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.direct_debits.direct_debits_schemas import (
    ChangeRequestRequest,
    ChangeRequestResponse,
    DirectDebitListResponse,
)
from app.direct_debits.direct_debits_service import DirectDebitService
from app.middleware.auth import get_current_user, require_step_up
from app.models.app_user import AppUser
from app.models.user_session import UserSession

router = APIRouter(prefix="/api/v1/direct-debits", tags=["direct-debits"])


@router.get("", response_model=DirectDebitListResponse)
def get_direct_debits(
    account_id: int = Query(..., description="Account ID to filter mandates"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user)
):
    """
    Get all direct debit mandates for an account.
    
    Returns list of mandates ordered by created_at DESC.
    """
    service = DirectDebitService(db)
    return service.get_mandates(account_id=account_id)


@router.post("/change-requests", response_model=ChangeRequestResponse, status_code=201)
def create_change_request(
    request: ChangeRequestRequest = Body(...),
    db: Session = Depends(get_db),
    user_session: tuple[AppUser, UserSession] = Depends(require_step_up)
):
    """
    Initiate a direct debit mandate change.
    
    Requires step-up authentication with scope 'direct_debit_change'.
    Enforces unique (mandate_id, idempotency_key) constraint.
    """
    user, session = user_session

    service = DirectDebitService(db)
    result = service.initiate_change(
        mandate_id=request.mandate_id,
        change_type=request.change_type,
        new_payment_amount=request.new_payment_amount,
        idempotency_key=request.idempotency_key,
        user_id=user.id,
        step_up_verified=True
    )
    
    db.commit()
    return result

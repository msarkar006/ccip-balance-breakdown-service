"""
Payment router - API endpoints for payment history and initiation.
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_step_up
from app.models.app_user import AppUser
from app.models.user_session import UserSession
from app.payments.payments_schemas import (
    PaymentCancellationResponse,
    PaymentDetailResponse,
    PaymentGuidanceResponse,
    PaymentInitiationRequest,
    PaymentInitiationResponse,
    PaymentListResponse,
)
from app.payments.payments_service import PaymentService

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.get("", response_model=PaymentListResponse)
def get_payments(
    account_id: int = Query(..., description="Account ID to filter payments"),
    payment_type: Optional[str] = Query(None, description="Payment type filter: Scheduled, OneOff, DirectDebitCollection"),
    limit: int = Query(25, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user)
):
    """
    Get paginated payment history for an account.

    Payments are ordered by scheduled_date DESC, then created_at DESC.
    """
    service = PaymentService(db)
    return service.get_payments(
        account_id=account_id,
        payment_type=payment_type,
        limit=limit,
        offset=offset
    )


@router.get("/guidance", response_model=PaymentGuidanceResponse)
def get_payment_guidance(
    account_id: int = Query(..., description="Account ID for guidance"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user)
):
    """
    Get payment guidance with balance and direct debit coverage.

    Returns minimum payment, due date, current balance, max payment amount,
    and DirectDebitService.derive_coverage coverage interpretation.
    """
    service = PaymentService(db)
    return service.get_payment_guidance(account_id=account_id)


@router.post("", response_model=PaymentInitiationResponse, status_code=201)
def initiate_payment(
    request: PaymentInitiationRequest = Body(...),
    db: Session = Depends(get_db),
    user_session: tuple[AppUser, UserSession] = Depends(require_step_up)
):
    """
    Initiate a one-off or scheduled payment.

    Requires step-up authentication with scope 'payment'.
    Validates amount > 0 and amount ≤ current balance.
    Enforces unique (account_id, idempotency_key) constraint.
    Calls risk adapter and submits to PaymentRailAdapter when allowed.
    Returns 201 with outcome and guidance.
    """
    user, session = user_session

    service = PaymentService(db)
    return service.initiate_payment(
        account_id=request.account_id,
        amount=request.amount,
        currency=request.currency,
        payment_method=request.payment_method,
        scheduled_date=request.scheduled_date,
        idempotency_key=request.idempotency_key,
        user_id=user.id,
        step_up_verified=True
    )


@router.get("/{id}", response_model=PaymentDetailResponse)
def get_payment_detail(
    id: int = Path(..., description="Payment ID"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user)
):
    """
    Get detailed payment with timeline and cancellation availability.

    Returns payment resource, tracking events timeline, can_cancel flag,
    cancellation_message, and guidance for non-final/failed states.
    """
    service = PaymentService(db)
    return service.get_payment_detail(payment_id=id)


@router.post("/{id}/cancel", response_model=PaymentCancellationResponse, status_code=200)
def cancel_payment(
    id: int = Path(..., description="Payment ID"),
    db: Session = Depends(get_db),
    user_session: tuple[AppUser, UserSession] = Depends(require_step_up)
):
    """
    Cancel a scheduled or pending payment.

    Requires step-up authentication with scope 'payment_cancellation'.
    Only payments with status 'Submitted' or 'Processing' that have not been
    submitted to the payment rail can be cancelled.

    Returns 200 with cancellation confirmation.
    Returns 403 if step-up verification fails.
    Returns 404 if payment not found.
    Returns 422 if payment cannot be cancelled.
    """
    user, session = user_session

    service = PaymentService(db)
    return service.cancel_payment(payment_id=id, user_id=user.id)

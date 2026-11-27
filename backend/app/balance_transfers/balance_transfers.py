"""
Balance transfer API routes - balance transfer tracking and initiation endpoints.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.balance_transfers.balance_transfers_schemas import (
    BalanceTransferDetailResponse,
    BalanceTransferInitiationRequest,
    BalanceTransferInitiationResponse,
    BalanceTransferListResponse,
)
from app.balance_transfers.balance_transfers_service import BalanceTransferService
from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.app_user import AppUser
from app.models.user_session import UserSession

router = APIRouter(prefix="/api/v1/balance-transfers", tags=["balance-transfers"])


@router.get("", response_model=BalanceTransferListResponse)
def get_balance_transfers(
    account_id: Annotated[int, Query(..., description="Account ID to filter transfers")],
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of results")] = 10,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip")] = 0,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> BalanceTransferListResponse:
    """
    Get paginated balance transfer history for an account.

    Returns transfers ordered by requested_on DESC (created_at DESC).
    """
    service = BalanceTransferService(db)
    return service.get_history(account_id=account_id, limit=limit, offset=offset)


@router.get("/{id}", response_model=BalanceTransferDetailResponse)
def get_balance_transfer_detail(
    id: int,
    account_id: Annotated[int, Query(..., description="Account ID for ownership verification")],
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> BalanceTransferDetailResponse:
    """
    Get detailed balance transfer with timeline, promotional context, and guidance.

    Returns:
        - Transfer resource
        - Timeline from tracking_events
        - Promotional context (promo_rate, promo_start_date, promo_end_date, revert_rate)
        - Linked balance category via source_link
        - Guidance for Rejected or unresolved states
    """
    service = BalanceTransferService(db)
    return service.get_detail(transfer_id=id, account_id=account_id)


@router.post("", response_model=BalanceTransferInitiationResponse, status_code=201)
def initiate_balance_transfer(
    request: BalanceTransferInitiationRequest,
    idempotency_key: Annotated[str, Header(..., alias="Idempotency-Key")],
    x_step_up_proof: Annotated[str | None, Header(alias="X-Step-Up-Proof")] = None,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> BalanceTransferInitiationResponse:
    """
    Initiate a balance transfer.

    Required headers:
        - Idempotency-Key: Unique key for idempotent replay
        - X-Step-Up-Proof: Step-up authentication proof (required)

    Pipeline execution:
        1. Ownership check
        2. Step-up verification (scope: balance_transfer)
        3. Schema validation
        4. Idempotency lookup
        5. Business rules (offer eligibility, amount <= available_credit)
        6. Risk decision
        7. Rail submission (when allow)
        8. Atomic commit + first tracking event
        9. Publish event + audit

    Returns:
        - 201 with outcome (Submitted, ReviewRequired, Rejected) + guidance
        - 200 with idempotent_replay=true for replay
        - 403 if step-up missing/stale/wrong scope
        - 422 if validation fails
    """
    # Get user session for step-up verification

    # We need the session to check step-up, but we already have current_user
    # For now, we'll query the session directly
    session = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at.is_(None)
    ).order_by(UserSession.created_at.desc()).first()

    from fastapi import Response as FastAPIResponse
    
    service = BalanceTransferService(db)
    request.idempotency_key = idempotency_key

    result = service.initiate_transfer(
        request=request,
        user_id=current_user.id,
        step_up_verified_at=session.step_up_verified_at if session else None
    )
    
    db.commit()
    
    # Return 200 for idempotent replay, 201 for new creation
    if result.idempotent_replay:
        return FastAPIResponse(
            content=result.model_dump_json(),
            media_type="application/json",
            status_code=200
        )
    
    return result

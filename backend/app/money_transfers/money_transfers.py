"""
Money transfer API routes - money transfer tracking and initiation endpoints.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.app_user import AppUser
from app.models.user_session import UserSession
from app.money_transfers.money_transfers_schemas import (
    MoneyTransferDetailResponse,
    MoneyTransferInitiationRequest,
    MoneyTransferInitiationResponse,
    MoneyTransferListResponse,
    PayeeListResponse,
)
from app.money_transfers.money_transfers_service import MoneyTransferService

router = APIRouter(prefix="/api/v1/money-transfers", tags=["money-transfers"])
payee_router = APIRouter(prefix="/api/v1/payees", tags=["payees"])


@router.get("", response_model=MoneyTransferListResponse)
def get_money_transfers(
    account_id: Annotated[int, Query(..., description="Account ID to filter transfers")],
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of results")] = 10,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip")] = 0,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> MoneyTransferListResponse:
    """
    Get paginated money transfer history for an account.

    Returns transfers ordered by requested_on DESC (created_at DESC).
    """
    service = MoneyTransferService(db)
    return service.get_history(account_id=account_id, limit=limit, offset=offset)


@router.get("/{id}", response_model=MoneyTransferDetailResponse)
def get_money_transfer_detail(
    id: int,
    account_id: Annotated[int, Query(..., description="Account ID for ownership verification")],
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> MoneyTransferDetailResponse:
    """
    Get detailed money transfer with timeline and guidance.

    Returns:
        - Transfer resource with payee details
        - Timeline from tracking_events
        - Guidance for Failed, Rejected, Delayed, or Blocked states
    """
    service = MoneyTransferService(db)
    return service.get_detail(transfer_id=id, account_id=account_id)


@router.post("", response_model=MoneyTransferInitiationResponse, status_code=201)
def initiate_money_transfer(
    request: MoneyTransferInitiationRequest,
    idempotency_key: Annotated[str, Header(..., alias="Idempotency-Key")],
    x_step_up_proof: Annotated[str | None, Header(alias="X-Step-Up-Proof")] = None,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> MoneyTransferInitiationResponse:
    """
    Initiate a money transfer.

    Required headers:
        - Idempotency-Key: Unique key for idempotent replay
        - X-Step-Up-Proof: Step-up authentication proof (required)

    Pipeline execution:
        1. Ownership check
        2. Step-up verification (scope: money_transfer)
        3. Schema validation
        4. Idempotency lookup
        5. Business rules (payee ownership, amount+fee <= available_credit)
        6. Risk decision
        7. Rail submission (when allow)
        8. Atomic commit + first tracking event
        9. Publish event + audit

    Returns:
        - 201 with outcome (Submitted, Rejected, Blocked) + guidance
        - 200 with idempotent_replay=true for replay
        - 403 if step-up missing/stale/wrong scope
        - 422 if validation fails
    """
    # Get user session for step-up verification
    session = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at.is_(None)
    ).order_by(UserSession.created_at.desc()).first()

    from fastapi import Response as FastAPIResponse
    
    service = MoneyTransferService(db)
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


@payee_router.get("", response_model=PayeeListResponse)
def get_payees(
    account_id: Annotated[int, Query(..., description="Account ID to filter payees")],
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of results")] = 25,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip")] = 0,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> PayeeListResponse:
    """
    Get paginated list of customer-owned payees with masked sort code and account number.

    Returns payees ordered by created_at DESC.
    """
    service = MoneyTransferService(db)
    return service.get_payees(account_id=account_id, limit=limit, offset=offset)

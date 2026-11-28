"""Balance breakdown endpoints (read-only)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.balance_schemas import BalanceBreakdownOut, BalanceBreakdownPage
from app.schemas.common_schemas import DEFAULT_LIMIT, MAX_LIMIT
from app.services.balance_service import BalanceService
from app.services.ownership import OwnershipScope, get_ownership_scope

router = APIRouter(tags=["balances"])


@router.get(
    "/accounts/{account_id}/balance-breakdowns",
    response_model=BalanceBreakdownPage,
    response_model_by_alias=True,
)
def list_balance_breakdowns(
    account_id: uuid.UUID,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    scope: OwnershipScope = Depends(get_ownership_scope),
    db: Session = Depends(get_db),
) -> BalanceBreakdownPage:
    return BalanceService(db, scope).list_for_account(account_id, limit, offset)


@router.get(
    "/balance-breakdowns/{breakdown_id}",
    response_model=BalanceBreakdownOut,
    response_model_by_alias=True,
)
def get_balance_breakdown(
    breakdown_id: uuid.UUID,
    scope: OwnershipScope = Depends(get_ownership_scope),
    db: Session = Depends(get_db),
) -> BalanceBreakdownOut:
    return BalanceService(db, scope).get(breakdown_id)

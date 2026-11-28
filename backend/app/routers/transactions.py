"""Transaction list endpoint (read-only)."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common_schemas import DEFAULT_LIMIT, MAX_LIMIT
from app.schemas.transaction_schemas import TransactionOut, TransactionPage
from app.services.ownership import OwnershipScope, get_ownership_scope
from app.services.transaction_service import TransactionService

router = APIRouter(tags=["transactions"])


@router.get(
    "/accounts/{account_id}/transactions",
    response_model=TransactionPage,
    response_model_by_alias=True,
)
def list_transactions(
    account_id: uuid.UUID,
    transaction_status: Literal["Pending", "Posted"] | None = Query(None, alias="transactionStatus"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    scope: OwnershipScope = Depends(get_ownership_scope),
    db: Session = Depends(get_db),
) -> TransactionPage:
    return TransactionService(db, scope).list_transactions(account_id, transaction_status, limit, offset)


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionOut,
    response_model_by_alias=True,
)
def get_transaction(
    transaction_id: uuid.UUID,
    scope: OwnershipScope = Depends(get_ownership_scope),
    db: Session = Depends(get_db),
) -> TransactionOut:
    return TransactionService(db, scope).get_transaction(transaction_id)

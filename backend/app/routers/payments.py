"""Payment history endpoint (read-only)."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common_schemas import DEFAULT_LIMIT, MAX_LIMIT
from app.schemas.payment_schemas import PaymentOut, PaymentPage
from app.services.ownership import OwnershipScope, get_ownership_scope
from app.services.payment_service import PaymentService

router = APIRouter(tags=["payments"])


@router.get(
    "/accounts/{account_id}/payments",
    response_model=PaymentPage,
    response_model_by_alias=True,
)
def list_payments(
    account_id: uuid.UUID,
    payment_type: Literal["OneOff", "Scheduled", "DirectDebitCollection"] | None = Query(
        None, alias="paymentType"
    ),
    payment_status: Literal["Completed", "Processing", "Failed", "Submitted", "Cancelled"] | None = Query(
        None, alias="paymentStatus"
    ),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    scope: OwnershipScope = Depends(get_ownership_scope),
    db: Session = Depends(get_db),
) -> PaymentPage:
    return PaymentService(db, scope).list_payments(account_id, payment_type, payment_status, limit, offset)


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentOut,
    response_model_by_alias=True,
)
def get_payment(
    payment_id: uuid.UUID,
    scope: OwnershipScope = Depends(get_ownership_scope),
    db: Session = Depends(get_db),
) -> PaymentOut:
    return PaymentService(db, scope).get_payment(payment_id)

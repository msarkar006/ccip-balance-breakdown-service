"""Account overview endpoints (read-only)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.account_schemas import AccountOut, AccountPage
from app.schemas.card_schemas import CardPage
from app.schemas.common_schemas import DEFAULT_LIMIT, MAX_LIMIT
from app.services.account_service import AccountService
from app.services.ownership import OwnershipScope, get_ownership_scope

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=AccountPage, response_model_by_alias=True)
def list_accounts(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    scope: OwnershipScope = Depends(get_ownership_scope),
    db: Session = Depends(get_db),
) -> AccountPage:
    return AccountService(db, scope).list_accounts(limit, offset)


@router.get("/{account_id}", response_model=AccountOut, response_model_by_alias=True)
def get_account(
    account_id: uuid.UUID,
    scope: OwnershipScope = Depends(get_ownership_scope),
    db: Session = Depends(get_db),
) -> AccountOut:
    return AccountService(db, scope).get_account(account_id)


@router.get("/{account_id}/cards", response_model=CardPage, response_model_by_alias=True)
def list_account_cards(
    account_id: uuid.UUID,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    scope: OwnershipScope = Depends(get_ownership_scope),
    db: Session = Depends(get_db),
) -> CardPage:
    return AccountService(db, scope).list_cards(account_id, limit, offset)

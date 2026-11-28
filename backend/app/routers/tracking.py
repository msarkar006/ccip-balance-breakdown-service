"""Tracking events endpoint (read-only)."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common_schemas import DEFAULT_LIMIT, MAX_LIMIT
from app.schemas.tracking_event_schemas import TrackingEventPage
from app.services.ownership import OwnershipScope, get_ownership_scope
from app.services.tracking_service import TrackingService

router = APIRouter(tags=["tracking"])


@router.get(
    "/accounts/{account_id}/tracking-events",
    response_model=TrackingEventPage,
    response_model_by_alias=True,
)
def list_tracking_events(
    account_id: uuid.UUID,
    tracked_entity_type: Literal["account", "transaction", "payment"] | None = Query(
        None, alias="trackedEntityType"
    ),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    scope: OwnershipScope = Depends(get_ownership_scope),
    db: Session = Depends(get_db),
) -> TrackingEventPage:
    return TrackingService(db, scope).list_events(account_id, tracked_entity_type, limit, offset)

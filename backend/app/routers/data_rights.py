"""Audited data-rights requests (record only; no fulfilment operation is exposed)."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common_schemas import DEFAULT_LIMIT, MAX_LIMIT
from app.schemas.data_rights_schemas import (
    DataRightsRequestCreate,
    DataRightsRequestOut,
    DataRightsRequestPage,
)
from app.services.auth_service import CurrentUser
from app.services.data_rights_service import DataRightsService

router = APIRouter(tags=["data-rights"])


@router.post(
    "/data-rights-requests",
    response_model=DataRightsRequestOut,
    response_model_by_alias=True,
    status_code=201,
)
def create_data_rights_request(
    payload: DataRightsRequestCreate,
    response: Response,
    idempotency_key: str = Header(
        ..., alias="Idempotency-Key", min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"
    ),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataRightsRequestOut:
    result, replayed = DataRightsService(db, user).create(payload, idempotency_key)
    if replayed:
        response.status_code = 200
        response.headers["Idempotent-Replayed"] = "true"
    return result


@router.get(
    "/data-rights-requests",
    response_model=DataRightsRequestPage,
    response_model_by_alias=True,
)
def list_data_rights_requests(
    status: Literal["received", "in_progress", "fulfilled", "declined"] | None = Query(None),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataRightsRequestPage:
    return DataRightsService(db, user).list_requests(status, limit, offset)


@router.get(
    "/data-rights-requests/{request_id}",
    response_model=DataRightsRequestOut,
    response_model_by_alias=True,
)
def get_data_rights_request(
    request_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataRightsRequestOut:
    return DataRightsService(db, user).get_request(request_id)

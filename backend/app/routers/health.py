"""Health router: liveness (no database) and readiness (trivial query). Mounted at the root."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import DomainError

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    status: Literal["ok"]


class ReadinessFailedError(DomainError):
    status_code = 500
    public_detail = "Internal server error"


@router.get("/health", response_model=HealthStatus, operation_id="getLiveness")
def liveness() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/health/ready", response_model=HealthStatus, operation_id="getReadiness")
def readiness(db: Session = Depends(get_db)) -> HealthStatus:
    try:
        db.execute(select(1)).scalar_one()
    except SQLAlchemyError as exc:
        raise ReadinessFailedError("database readiness check failed") from exc
    return HealthStatus(status="ok")

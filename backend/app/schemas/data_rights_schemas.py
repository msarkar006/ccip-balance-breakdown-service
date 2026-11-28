"""Data-rights request schemas (camelCase on the wire)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field

from app.schemas.common_schemas import ApiModel, Page

RequestType = Literal["export", "deletion"]
RequestStatus = Literal["received", "in_progress", "fulfilled", "declined"]


class DataRightsRequestCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    request_type: RequestType
    subject_ref: str | None = Field(default=None, min_length=1, max_length=40)


class DataRightsRequestOut(ApiModel):
    id: uuid.UUID
    subject_ref: str
    request_type: RequestType
    status: RequestStatus
    requested_at: datetime
    due_at: datetime
    completed_at: datetime | None = None
    outcome_summary: str | None = None


DataRightsRequestPage = Page[DataRightsRequestOut]

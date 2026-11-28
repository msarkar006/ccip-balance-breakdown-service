"""Tracking event schemas: source values verbatim plus a freshness label."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from app.schemas.common_schemas import ApiModel, Freshness, Page

TrackedEntityType = Literal["account", "transaction", "payment"]


class TrackingEventOut(ApiModel):
    id: uuid.UUID
    account_id: uuid.UUID
    transaction_id: uuid.UUID | None = None
    payment_id: uuid.UUID | None = None
    tracked_entity_type: TrackedEntityType
    tracked_entity_id: uuid.UUID
    lifecycle_status: str
    source_time: datetime | None = None
    provenance: str
    occurred_at: datetime
    freshness: Freshness


TrackingEventPage = Page[TrackingEventOut]

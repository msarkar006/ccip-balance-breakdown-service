"""Tracking events: source time and lifecycle verbatim; no inferred transition or completion time."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import TrackingEvent
from app.repositories.account_repository import AccountRepository
from app.repositories.setting_repository import SettingsRepository
from app.repositories.tracking_repository import TrackingRepository
from app.schemas.tracking_event_schemas import TrackingEventOut, TrackingEventPage
from app.services.freshness_interpreter import FreshnessInterpreter
from app.services.ownership import OwnershipScope


class TrackingService:
    def __init__(self, db: Session, scope: OwnershipScope) -> None:
        self.scope = scope
        self.accounts = AccountRepository(db)
        self.repo = TrackingRepository(db)
        self.freshness = FreshnessInterpreter(SettingsRepository(db))

    def list_events(
        self, account_id: uuid.UUID, entity_type: str | None, limit: int, offset: int
    ) -> TrackingEventPage:
        account = self.accounts.get_for_customer(self.scope.customer_id, account_id)
        if account is None:
            raise NotFoundError("account not found for this customer")
        rows, total = self.repo.list_for_account(account.id, entity_type, limit, offset)
        return TrackingEventPage(items=[self._to_out(e) for e in rows], total=total, limit=limit, offset=offset)

    def _to_out(self, e: TrackingEvent) -> TrackingEventOut:
        return TrackingEventOut(
            id=e.id,
            account_id=e.account_id,
            transaction_id=e.transaction_id,
            payment_id=e.payment_id,
            tracked_entity_type=e.tracked_entity_type,
            tracked_entity_id=e.tracked_entity_id,
            lifecycle_status=e.lifecycle_status,
            source_time=e.source_time,
            provenance=e.provenance,
            occurred_at=e.occurred_at,
            freshness=self.freshness.for_kind("tracking_event", e.source_time),
        )

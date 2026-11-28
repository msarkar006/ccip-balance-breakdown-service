"""Algorithm D: idempotent, audited data-rights request creation. Records the request only."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import DomainError, ForbiddenError, NotFoundError
from app.models import Customer, DataRightsRequest
from app.repositories.data_rights_repository import DataRightsRepository
from app.repositories.setting_repository import SettingsRepository
from app.schemas.data_rights_schemas import (
    DataRightsRequestCreate,
    DataRightsRequestOut,
    DataRightsRequestPage,
)
from app.services.audit_service import AuditService
from app.services.auth_service import CurrentUser
from app.utils import to_utc

DEFAULT_FULFILMENT_DAYS = 30


class BadRequestError(DomainError):
    status_code = 400
    public_detail = "Idempotency key was already used with a different request"


class DataRightsService:
    def __init__(self, db: Session, user: CurrentUser) -> None:
        self.db = db
        self.user = user
        self.repo = DataRightsRepository(db)
        self.audit = AuditService(db)
        self.settings = SettingsRepository(db)

    def create(
        self, payload: DataRightsRequestCreate, idempotency_key: str
    ) -> tuple[DataRightsRequestOut, bool]:
        """Return (request, replayed)."""
        subject = self._resolve_subject(payload.subject_ref)

        existing = self.repo.find_by_key(self.user.id, idempotency_key)
        if existing is not None:
            return self._replay(existing, payload, subject), True

        requested_at = datetime.now(UTC)
        days = self.settings.get_int("data_rights.fulfilment_days", DEFAULT_FULFILMENT_DAYS)
        if days < 1:
            days = DEFAULT_FULFILMENT_DAYS
        row = DataRightsRequest(
            subject_customer_id=subject.id,
            subject_ref=subject.source_ref,
            requested_by_user_id=self.user.id,
            request_type=payload.request_type,
            status="received",
            idempotency_key=idempotency_key,
            requested_at=requested_at,
            due_at=requested_at + timedelta(days=days),
        )
        try:
            self.repo.add(row)
            self.audit.record(
                event_type="data_rights_request_created",
                entity_type="data_rights_request",
                entity_id=str(row.id),
                actor_user_id=self.user.id,
                detail=f"type={payload.request_type} subject={subject.source_ref}",
            )
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            winner = self.repo.find_by_key(self.user.id, idempotency_key)
            if winner is None:
                raise
            return self._replay(winner, payload, subject), True
        return self._to_out(row), False

    def list_requests(self, status: str | None, limit: int, offset: int) -> DataRightsRequestPage:
        requester = None if self.user.role == "administrator" else self.user.id
        rows, total = self.repo.list_requests(requester, status, limit, offset)
        return DataRightsRequestPage(items=[self._to_out(r) for r in rows], total=total, limit=limit, offset=offset)

    def get_request(self, request_id: uuid.UUID) -> DataRightsRequestOut:
        row = self.repo.get(request_id)
        if row is None or (self.user.role != "administrator" and row.requested_by_user_id != self.user.id):
            raise NotFoundError("data-rights request not found")
        return self._to_out(row)

    def _resolve_subject(self, subject_ref: str | None) -> Customer:
        if self.user.role == "administrator":
            if subject_ref is None:
                raise NotFoundError("administrator must name a subject")
            subject = self.repo.get_customer_by_ref(subject_ref)
            if subject is None:
                raise NotFoundError("unknown subject")
            return subject
        own = self.repo.get_customer(self.user.customer_id) if self.user.customer_id else None
        if own is None:
            raise ForbiddenError("no subject for this user")
        if subject_ref is not None and subject_ref != own.source_ref:
            raise ForbiddenError("a customer may only raise a request for their own subject")
        return own

    def _replay(
        self, existing: DataRightsRequest, payload: DataRightsRequestCreate, subject: Customer
    ) -> DataRightsRequestOut:
        if existing.request_type != payload.request_type or existing.subject_ref != subject.source_ref:
            raise BadRequestError("idempotency key reused with a different body")
        return self._to_out(existing)

    @staticmethod
    def _to_out(r: DataRightsRequest) -> DataRightsRequestOut:
        return DataRightsRequestOut(
            id=r.id,
            subject_ref=r.subject_ref,
            request_type=r.request_type,
            status=r.status,
            requested_at=to_utc(r.requested_at) or r.requested_at,
            due_at=to_utc(r.due_at) or r.due_at,
            completed_at=to_utc(r.completed_at),
            outcome_summary=r.outcome_summary,
        )

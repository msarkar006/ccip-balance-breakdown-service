"""Parameterized access to `data_rights_requests` and the subject lookup."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Customer, DataRightsRequest


class DataRightsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_customer_by_ref(self, source_ref: str) -> Customer | None:
        return self.db.scalars(select(Customer).where(Customer.source_ref == source_ref)).first()

    def get_customer(self, customer_id: uuid.UUID) -> Customer | None:
        return self.db.get(Customer, customer_id)

    def find_by_key(self, user_id: uuid.UUID, key: str) -> DataRightsRequest | None:
        stmt = select(DataRightsRequest).where(
            DataRightsRequest.requested_by_user_id == user_id, DataRightsRequest.idempotency_key == key
        )
        return self.db.scalars(stmt).first()

    def get(self, request_id: uuid.UUID) -> DataRightsRequest | None:
        return self.db.get(DataRightsRequest, request_id)

    def add(self, row: DataRightsRequest) -> DataRightsRequest:
        self.db.add(row)
        self.db.flush()
        return row

    def list_requests(
        self, requester_id: uuid.UUID | None, status: str | None, limit: int, offset: int
    ) -> tuple[list[DataRightsRequest], int]:
        conditions = []
        if requester_id is not None:
            conditions.append(DataRightsRequest.requested_by_user_id == requester_id)
        if status is not None:
            conditions.append(DataRightsRequest.status == status)
        total = self.db.scalar(select(func.count()).select_from(DataRightsRequest).where(*conditions)) or 0
        stmt = (
            select(DataRightsRequest)
            .where(*conditions)
            .order_by(DataRightsRequest.requested_at.desc(), DataRightsRequest.id)
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt)), total

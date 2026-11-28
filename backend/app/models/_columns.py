"""Shared column helpers for the persistence models (generic Uuid, tz-aware UTC timestamps)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

UTC_DATETIME = DateTime(timezone=True)


def utcnow() -> datetime:
    return datetime.now(UTC)


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def created_at_column() -> Mapped[datetime]:
    return mapped_column(UTC_DATETIME, nullable=False, default=utcnow, server_default=text("CURRENT_TIMESTAMP"))


def updated_at_column() -> Mapped[datetime]:
    return mapped_column(
        UTC_DATETIME,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

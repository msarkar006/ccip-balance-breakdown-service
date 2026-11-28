"""Small pure helpers: UTC normalisation and mask checks."""

from __future__ import annotations

from datetime import UTC, datetime

from app.exceptions import MaskingViolationError

MASK_PREFIX = "****"


def to_utc(value: datetime | None) -> datetime | None:
    """Attach UTC to naive values (SQLite drops the offset); convert aware values to UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def mask_check(value: str | None) -> str | None:
    """Return a stored masked value unchanged, or raise if it does not start with `****`."""
    if value is None:
        return None
    if not value.startswith(MASK_PREFIX):
        raise MaskingViolationError("stored masked value failed mask_check")
    return value

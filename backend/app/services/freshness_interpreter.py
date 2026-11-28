"""Algorithm A: label a source timestamp. Never yields a fresh or real-time state."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from app.repositories.setting_repository import SettingsRepository
from app.schemas.common_schemas import Freshness
from app.schemas.tracking_schemas import FRESHNESS_SETTING_KEYS
from app.utils import to_utc


def _utc_now() -> datetime:
    return datetime.now(UTC)


class FreshnessInterpreter:
    def __init__(self, settings: SettingsRepository, clock: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.clock = clock

    @staticmethod
    def interpret(source_time: datetime | None, max_age_seconds: int | None, now: datetime) -> Freshness:
        if source_time is None:
            return Freshness(state="freshness unavailable", basis="no source timestamp")
        source = source_time.replace(tzinfo=UTC) if source_time.tzinfo is None else source_time.astimezone(UTC)
        if max_age_seconds is None:
            return Freshness(
                state="unconfirmed freshness",
                basis="timestamp present, no approved maximum age",
                source_time=source,
            )
        reference = to_utc(now) or now
        if (reference - source).total_seconds() >= max_age_seconds:
            return Freshness(
                state="stale",
                basis="approved threshold reached",
                source_time=source,
                max_age_seconds=max_age_seconds,
            )
        return Freshness(
            state="unconfirmed freshness",
            basis="approved threshold not reached",
            source_time=source,
            max_age_seconds=max_age_seconds,
        )

    def for_kind(self, kind: str, source_time: datetime | None) -> Freshness:
        key = FRESHNESS_SETTING_KEYS[kind]
        raw = self.settings.get_many([key])[key]
        try:
            max_age = int(raw) if raw is not None else None
        except ValueError:
            max_age = None
        if max_age is not None and max_age < 1:
            max_age = None
        return self.interpret(source_time, max_age, self.clock())

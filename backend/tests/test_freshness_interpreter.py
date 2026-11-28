from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import update

from app.models import AppSetting
from app.repositories.setting_repository import SettingsRepository
from app.services.freshness_interpreter import FreshnessInterpreter

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def test_unavailable_without_timestamp():
    f = FreshnessInterpreter.interpret(None, 60, NOW)
    assert f.state == "freshness unavailable"
    assert f.source_time is None


def test_unconfirmed_without_max_age():
    f = FreshnessInterpreter.interpret(NOW - timedelta(days=9), None, NOW)
    assert f.state == "unconfirmed freshness"
    assert f.max_age_seconds is None


def test_threshold_boundaries():
    t = NOW - timedelta(seconds=60)
    assert FreshnessInterpreter.interpret(t, 60, NOW).state == "stale"
    assert FreshnessInterpreter.interpret(t, 61, NOW).state == "unconfirmed freshness"


def test_naive_and_offset_times_normalised():
    naive = datetime(2026, 1, 1, 11, 0)
    f = FreshnessInterpreter.interpret(naive, 60, NOW)
    assert f.state == "stale" and f.source_time == naive.replace(tzinfo=UTC)
    plus2 = datetime(2026, 1, 1, 13, 0, tzinfo=timezone(timedelta(hours=2)))
    assert FreshnessInterpreter.interpret(plus2, 60, NOW).source_time == datetime(2026, 1, 1, 11, 0, tzinfo=UTC)


def test_uses_settings_and_injected_clock(db_session):
    repo = SettingsRepository(db_session)
    source = NOW - timedelta(seconds=500)
    interp = FreshnessInterpreter(repo, clock=lambda: NOW)
    # seeded migration value is not_set -> unconfirmed
    assert interp.for_kind("transaction", source).state == "unconfirmed freshness"
    db_session.execute(
        update(AppSetting)
        .where(AppSetting.setting_key == "freshness.max_age_seconds.transaction")
        .values(value_text="300", approval_status="approved")
    )
    db_session.commit()
    f = interp.for_kind("transaction", source)
    assert f.state == "stale" and f.max_age_seconds == 300
    later = FreshnessInterpreter(repo, clock=lambda: source + timedelta(seconds=10))
    assert later.for_kind("transaction", source).state == "unconfirmed freshness"
    assert repo.get_many(["freshness.max_age_seconds.tracking_event", "missing"]) == {
        "freshness.max_age_seconds.tracking_event": None,
        "missing": None,
    }

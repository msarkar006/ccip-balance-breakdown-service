"""Tracking events: order, filter, verbatim lifecycle and the three freshness states."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models import Account, AppSetting, TrackingEvent
from tests.conftest import login

KEY = "freshness.max_age_seconds.tracking_event"


def _account(db_session):  # type: ignore[no-untyped-def]
    return db_session.scalars(select(Account).where(Account.source_ref == "ACC-1001")).one()


def _url(account) -> str:  # type: ignore[no-untyped-def]
    return f"/api/v1/accounts/{account.id}/tracking-events"


def test_order_newest_first_and_page_shape(seeded, client, db_session):  # type: ignore[no-untyped-def]
    r = client.get(_url(_account(db_session)), headers=login(client))
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"items", "total", "limit", "offset"}
    times = [i["occurredAt"] for i in body["items"]]
    assert times == sorted(times, reverse=True)
    assert body["total"] == 3


def test_entity_type_filter_and_invalid_value(seeded, client, db_session):  # type: ignore[no-untyped-def]
    h = login(client)
    url = _url(_account(db_session))
    r = client.get(url, params={"trackedEntityType": "payment"}, headers=h)
    assert [i["trackedEntityType"] for i in r.json()["items"]] == ["payment"]
    assert client.get(url, params={"trackedEntityType": "card"}, headers=h).status_code == 422


def test_lifecycle_and_source_time_verbatim_no_inference(seeded, client, db_session):  # type: ignore[no-untyped-def]
    items = client.get(_url(_account(db_session)), headers=login(client)).json()["items"]
    by_type = {i["trackedEntityType"]: i for i in items}
    assert by_type["transaction"]["lifecycleStatus"] == "Pending"
    assert by_type["transaction"]["sourceTime"].startswith("2026-11-22T14:05")
    assert by_type["payment"]["lifecycleStatus"] == "Processing"
    assert by_type["payment"]["sourceTime"] is None
    assert "completedAt" not in by_type["payment"]


def test_freshness_absent_no_threshold_and_past_threshold(seeded, client, db_session):  # type: ignore[no-untyped-def]
    h = login(client)
    url = _url(_account(db_session))
    items = client.get(url, headers=h).json()["items"]
    by_type = {i["trackedEntityType"]: i for i in items}
    assert by_type["payment"]["freshness"]["state"] == "freshness unavailable"
    assert by_type["account"]["freshness"]["state"] == "unconfirmed freshness"  # no approved maximum age

    setting = db_session.scalars(select(AppSetting).where(AppSetting.setting_key == KEY)).one()
    setting.value_text = "60"
    setting.approval_status = "approved"
    db_session.commit()
    items = client.get(url, headers=h).json()["items"]
    states = {i["trackedEntityType"]: i["freshness"]["state"] for i in items}
    assert states["account"] == "stale"
    assert states["payment"] == "freshness unavailable"

    recent = TrackingEvent(
        account_id=_account(db_session).id,
        tracked_entity_type="account",
        tracked_entity_id=_account(db_session).id,
        lifecycle_status="Open",
        provenance="test",
        source_time=datetime.now(UTC) - timedelta(seconds=5),
    )
    db_session.add(recent)
    db_session.commit()
    items = client.get(url, params={"limit": 100}, headers=h).json()["items"]
    fresh = [i for i in items if i["provenance"] == "test"][0]
    assert fresh["freshness"]["state"] == "unconfirmed freshness"


def test_access_rules(seeded, client, db_session):  # type: ignore[no-untyped-def]
    url = _url(_account(db_session))
    assert client.get(url).status_code == 401
    assert client.get(url, headers=login(client, "admin01")).status_code == 403
    assert client.get(url, headers=login(client, "customer02")).status_code == 404
    assert client.get("/api/v1/accounts/not-a-uuid/tracking-events", headers=login(client)).status_code == 422

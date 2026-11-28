"""Data-rights requests: Algorithm D idempotency, subjects, audit content and visibility."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models import AuditLog, DataRightsRequest
from tests.conftest import login

URL = "/api/v1/data-rights-requests"


def _post(client, headers, key, body):  # type: ignore[no-untyped-def]
    return client.post(URL, json=body, headers={**headers, "Idempotency-Key": key})


def test_create_then_replay_then_mismatch(seeded, client, db_session):  # type: ignore[no-untyped-def]
    h = login(client)
    first = _post(client, h, "key-1", {"requestType": "export"})
    assert first.status_code == 201
    body = first.json()
    assert body["status"] == "received" and body["subjectRef"] == "CUS-1001"
    assert body["completedAt"] is None
    from datetime import datetime

    delta = datetime.fromisoformat(body["dueAt"]) - datetime.fromisoformat(body["requestedAt"])
    assert delta.days == 30

    again = _post(client, h, "key-1", {"requestType": "export"})
    assert again.status_code == 200
    assert again.headers["Idempotent-Replayed"] == "true"
    assert again.json()["id"] == body["id"]
    assert "Idempotent-Replayed" not in first.headers

    mismatch = _post(client, h, "key-1", {"requestType": "deletion"})
    assert mismatch.status_code == 400
    assert set(mismatch.json()) == {"detail"}

    count = db_session.scalar(
        select(func.count()).select_from(DataRightsRequest).where(DataRightsRequest.idempotency_key == "key-1")
    )
    assert count == 1


def test_audit_event_content_and_no_replay_event(seeded, client, db_session):  # type: ignore[no-untyped-def]
    h = login(client)
    rid = _post(client, h, "key-a", {"requestType": "deletion"}).json()["id"]
    _post(client, h, "key-a", {"requestType": "deletion"})
    rows = db_session.scalars(select(AuditLog).where(AuditLog.event_type == "data_rights_request_created")).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.entity_id == rid and row.entity_type == "data_rights_request"
    assert row.actor_user_id is not None and row.correlation_id
    assert "key-a" not in (row.detail or "") and "Bearer" not in (row.detail or "")


def test_foreign_subject_forbidden_own_subject_ok(seeded, client):  # type: ignore[no-untyped-def]
    h = login(client)
    assert _post(client, h, "k2", {"requestType": "export", "subjectRef": "CUS-2001"}).status_code == 403
    assert _post(client, h, "k3", {"requestType": "export", "subjectRef": "CUS-1001"}).status_code == 201


def test_administrator_must_name_known_subject(seeded, client):  # type: ignore[no-untyped-def]
    h = login(client, "admin01")
    assert _post(client, h, "a1", {"requestType": "export"}).status_code == 404
    assert _post(client, h, "a2", {"requestType": "export", "subjectRef": "CUS-9999"}).status_code == 404
    ok = _post(client, h, "a3", {"requestType": "export", "subjectRef": "CUS-2001"})
    assert ok.status_code == 201 and ok.json()["subjectRef"] == "CUS-2001"


def test_validation(seeded, client):  # type: ignore[no-untyped-def]
    h = login(client)
    assert client.post(URL, json={"requestType": "export"}, headers=h).status_code == 422  # no key
    assert _post(client, h, "k", {"requestType": "erase"}).status_code == 422
    assert _post(client, h, "k", {"requestType": "export", "extra": 1}).status_code == 422
    assert _post(client, h, "bad key!", {"requestType": "export"}).status_code == 422
    assert client.post(URL, json={"requestType": "export"}, headers={"Idempotency-Key": "x"}).status_code == 401


def test_list_scope_and_status_filter(seeded, client):  # type: ignore[no-untyped-def]
    h1 = login(client)
    page = client.get(URL, headers=h1).json()
    assert set(page) == {"items", "total", "limit", "offset"} and page["total"] == 2
    assert [i["status"] for i in client.get(URL, params={"status": "fulfilled"}, headers=h1).json()["items"]] == [
        "fulfilled"
    ]
    fulfilled = client.get(URL, params={"status": "fulfilled"}, headers=h1).json()["items"][0]
    assert fulfilled["completedAt"] is not None
    assert client.get(URL, params={"status": "bogus"}, headers=h1).status_code == 422
    assert client.get(URL, headers=login(client, "customer02")).json()["total"] == 0
    assert client.get(URL, headers=login(client, "admin01")).json()["total"] == 2
    assert client.get(URL).status_code == 401


def test_get_one_visibility(seeded, client):  # type: ignore[no-untyped-def]
    h1 = login(client)
    rid = client.get(URL, headers=h1).json()["items"][0]["id"]
    assert client.get(f"{URL}/{rid}", headers=h1).status_code == 200
    assert client.get(f"{URL}/{rid}", headers=login(client, "admin01")).status_code == 200
    assert client.get(f"{URL}/{rid}", headers=login(client, "customer02")).status_code == 404
    assert client.get(f"{URL}/{'0' * 8}-0000-0000-0000-{'0' * 12}", headers=h1).status_code == 404
    assert client.get(f"{URL}/zzz", headers=h1).status_code == 422
    assert client.get(f"{URL}/{rid}").status_code == 401

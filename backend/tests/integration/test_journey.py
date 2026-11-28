"""End-to-end journey over the real app: account -> cards -> balances -> transactions -> payments -> tracking."""

from __future__ import annotations

import re

from sqlalchemy import select

from app.models import Account
from tests.conftest import login

CARD_PAN_LIKE = re.compile(r"\d{12,}")


def _first_account(client, headers):  # type: ignore[no-untyped-def]
    page = client.get("/api/v1/accounts", headers=headers).json()
    return next(a for a in page["items"] if a["sourceRef"] == "ACC-1001")


def test_customer_journey_across_all_domains(seeded, client):  # type: ignore[no-untyped-def]
    headers = login(client, "customer01")
    account = _first_account(client, headers)
    aid = account["id"]
    # FR-ACO-001/003: distinct labelled fields; absent stays null
    for key in ("creditLimit", "availableCredit", "currentBalance", "standardPurchaseApr", "nextStatementDate"):
        assert key in account
    assert account["freshness"]["state"] == "freshness unavailable"

    # FR-ACO-002: masked card
    cards = client.get(f"/api/v1/accounts/{aid}/cards", headers=headers).json()["items"]
    assert cards and all(c["maskedPan"].startswith("****") for c in cards)
    assert cards[0]["cardStatus"] == "Active"

    # FR-BAL-001..003 / FR-TRK-001
    listing = client.get(f"/api/v1/accounts/{aid}/balance-breakdowns", headers=headers).json()["items"]
    detail = client.get(f"/api/v1/balance-breakdowns/{listing[0]['id']}", headers=headers).json()
    assert detail["asOf"] and detail["pendingTotal"] is not None
    ranks = [c["displayRank"] for c in detail["categories"]]
    assert ranks == sorted(ranks) and len(ranks) == 5
    assert detail["freshness"]["state"] in {"unconfirmed freshness", "stale"}
    assert any(c.get("qualifierNotice") for c in detail["categories"])

    # FR-TRN-001..003 / FR-TRK-002
    txns = client.get(f"/api/v1/accounts/{aid}/transactions", headers=headers).json()["items"]
    assert {t["accountId"] for t in txns} == {aid}
    pending = [t for t in txns if t["transactionStatus"] == "Pending"]
    posted = [t for t in txns if t["transactionStatus"] == "Posted"]
    assert pending and posted
    assert all(t["postedDate"] is None for t in pending)
    assert all(t["postedDate"] and t["transactionTime"] for t in posted[:1])
    assert all((t["maskedPan"] or "****").startswith("****") for t in txns)
    one = client.get(f"/api/v1/transactions/{pending[0]['id']}", headers=headers).json()
    assert one["postedDate"] is None and one["transactionStatus"] == "Pending"

    # FR-PAY-001..003
    pays = client.get(f"/api/v1/accounts/{aid}/payments", headers=headers).json()["items"]
    assert {p["paymentStatus"] for p in pays} >= {"Completed", "Processing"}
    assert all(p["sourceMaskedAccount"].startswith("*") for p in pays if p["sourceMaskedAccount"])
    assert all(p["freshness"]["state"] == "freshness unavailable" for p in pays)
    assert "information" in pays[0]["informationalNotice"].lower()
    for method in ("post", "put", "patch", "delete"):
        assert getattr(client, method)(f"/api/v1/accounts/{aid}/payments", headers=headers).status_code in (404, 405)

    # FR-TRK-003/004
    events = client.get(f"/api/v1/accounts/{aid}/tracking-events", headers=headers).json()["items"]
    assert {e["lifecycleStatus"] for e in events} >= {"Open", "Pending", "Processing"}
    assert any(e["sourceTime"] is None for e in events)
    assert all(e["freshness"]["state"] != "fresh" for e in events)

    # no unmasked long digit runs anywhere
    for payload in (cards, txns, pays):
        assert not CARD_PAN_LIKE.search(str(payload))


def test_ownership_isolation_and_safe_errors(seeded, client, db_session):  # type: ignore[no-untyped-def]
    other = db_session.scalars(select(Account).where(Account.source_ref == "ACC-1003")).one()
    c1 = login(client, "customer01")
    mine = {a["id"] for a in client.get("/api/v1/accounts", headers=c1).json()["items"]}
    if str(other.id) not in mine:
        for path in ("", "/cards", "/transactions", "/payments", "/balance-breakdowns", "/tracking-events"):
            r = client.get(f"/api/v1/accounts/{other.id}{path}", headers=c1)
            assert r.status_code == 404 and set(r.json()) == {"detail"}
    r = client.get("/api/v1/accounts")
    assert r.status_code == 401 and set(r.json()) == {"detail"}


def test_correlation_id_propagates_to_response_and_audit(seeded, client, db_session):  # type: ignore[no-untyped-def]
    from app.models import AuditLog
    from app.seed_data.users import PERSONAS

    creds = PERSONAS["customer01"]
    r = client.post(
        "/api/v1/auth/login",
        json={"username": creds.username, "password": creds.password},
        headers={"X-Correlation-ID": "integration-corr-0001"},
    )
    assert r.status_code == 200 and r.headers["X-Correlation-ID"] == "integration-corr-0001"
    row = db_session.scalars(select(AuditLog).where(AuditLog.event_type == "login_success")).one()
    assert row.correlation_id == "integration-corr-0001"
    assert "password" not in str(row.detail).lower() and r.json()["accessToken"] not in str(row.detail)


def test_session_revocation_blocks_every_read(seeded, client, db_session):  # type: ignore[no-untyped-def]
    headers = login(client, "customer01")
    aid = _first_account(client, headers)["id"]
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    for path in ("", "/cards", "/transactions", "/payments", "/balance-breakdowns", "/tracking-events"):
        assert client.get(f"/api/v1/accounts/{aid}{path}", headers=headers).status_code == 401


def test_admin_limited_to_data_rights(seeded, client):  # type: ignore[no-untyped-def]
    headers = login(client, "admin01")
    assert client.get("/api/v1/accounts", headers=headers).status_code == 403
    assert client.get("/api/v1/data-rights-requests", headers=headers).status_code == 200


def test_data_rights_roundtrip_and_audit(seeded, client, db_session):  # type: ignore[no-untyped-def]
    from app.models import AuditLog

    headers = {**login(client, "customer01"), "Idempotency-Key": "integration-key-0001", "X-Correlation-ID": "dr-int-1"}
    body = {"requestType": "export"}
    first = client.post("/api/v1/data-rights-requests", json=body, headers=headers)
    assert first.status_code == 201 and first.json()["status"] == "received"
    again = client.post("/api/v1/data-rights-requests", json=body, headers=headers)
    assert again.status_code == 200 and again.headers.get("Idempotent-Replayed") == "true"
    ids = [r["id"] for r in client.get("/api/v1/data-rights-requests", headers=headers).json()["items"]]
    assert first.json()["id"] in ids
    rows = db_session.scalars(select(AuditLog).where(AuditLog.event_type == "data_rights_request_created")).all()
    assert len(rows) == 1 and rows[0].correlation_id == "dr-int-1"

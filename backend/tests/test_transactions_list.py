from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models import Account
from tests.conftest import login
from tests.factories import make_card, make_transaction


def _acc(db, ref):
    return db.scalar(select(Account).where(Account.source_ref == ref))


def _url(db, ref="ACC-1001", q=""):
    return f"/api/v1/accounts/{_acc(db, ref).id}/transactions{q}"


def test_seeded_list_pending_posted_masked(seeded, client, db_session):
    h = login(client, "customer01")
    r = client.get(_url(db_session), headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 4 and body["limit"] and body["offset"] == 0
    times = [i["transactionTime"] for i in body["items"]]
    assert times == sorted(times, reverse=True)
    first = body["items"][0]
    assert first["transactionStatus"] == "Pending" and first["postedDate"] is None
    assert first["maskedPan"] == "**** 4821" and first["transactionAmount"] == "42.15"
    assert first["freshness"]["state"] == "unconfirmed freshness"
    assert any(i["eligibleForInstalment"] is True for i in body["items"])
    assert any(i["transactionStatus"] == "Posted" and i["postedDate"] == "2026-11-21" for i in body["items"])
    assert "pan" not in first and "cardNumber" not in first


def test_empty_account(seeded, client, db_session):
    r = client.get(_url(db_session, "ACC-1002"), headers=login(client, "customer01"))
    assert r.status_code == 200 and r.json()["items"] == [] and r.json()["total"] == 0


def test_status_filter(seeded, client, db_session):
    h = login(client, "customer01")
    r = client.get(_url(db_session, q="?transactionStatus=Posted"), headers=h)
    assert r.json()["total"] == 2
    assert {i["transactionStatus"] for i in r.json()["items"]} == {"Posted"}
    assert client.get(_url(db_session, q="?transactionStatus=Settled"), headers=h).status_code == 422


def test_paging_and_id_tiebreak(seeded, client, db_session):
    acc = _acc(db_session, "ACC-1002")
    t = datetime(2026, 5, 1, tzinfo=UTC)
    rows = [make_transaction(db_session, acc, transaction_time=t) for _ in range(3)]
    make_transaction(db_session, acc, transaction_time=t - timedelta(days=1))
    h = login(client, "customer01")
    base = _url(db_session, "ACC-1002")
    ids = [i["id"] for i in client.get(base, headers=h).json()["items"][:3]]
    assert ids == sorted((str(r.id) for r in rows), reverse=True)
    page = client.get(base + "?limit=2&offset=2", headers=h).json()
    assert len(page["items"]) == 2 and page["total"] == 4 and page["offset"] == 2
    assert page["items"][0]["id"] == ids[2]


def test_validation_and_auth(seeded, client, db_session):
    assert client.get(_url(db_session)).status_code == 401
    h = login(client, "customer01")
    for q in ("?limit=0", "?limit=101", "?offset=-1", "?limit=x"):
        assert client.get(_url(db_session, q=q), headers=h).status_code == 422
    assert client.get("/api/v1/accounts/not-a-uuid/transactions", headers=h).status_code == 422


def test_ownership_and_admin(seeded, client, db_session):
    assert client.get(_url(db_session), headers=login(client, "customer02")).status_code == 404
    assert client.get(_url(db_session), headers=login(client, "admin01")).status_code == 403


def test_only_selected_account_and_null_card(seeded, client, db_session):
    acc = _acc(db_session, "ACC-1003")
    make_card(db_session, acc, masked_pan="**** 9040")
    make_transaction(db_session, acc, merchant_name="NOCARD")
    h = login(client, "customer01")
    items = client.get(_url(db_session, "ACC-1003"), headers=h).json()["items"]
    assert [i["merchantName"] for i in items] == ["NOCARD"]
    assert items[0]["maskedPan"] is None and items[0]["cardId"] is None

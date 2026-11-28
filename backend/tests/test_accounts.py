from __future__ import annotations

from sqlalchemy import select

from app.models import Account
from tests.conftest import login


def _by_ref(client, headers):
    page = client.get("/api/v1/accounts", headers=headers).json()
    return {item["sourceRef"]: item for item in page["items"]}, page


def test_list_envelope_and_scope(seeded, client):
    items, page = _by_ref(client, login(client, "customer01"))
    assert set(items) == {"ACC-1001", "ACC-1002", "ACC-1003"}
    assert page["total"] == 3 and page["limit"] == 25 and page["offset"] == 0


def test_account_fields_distinct_and_verbatim(seeded, client):
    headers = login(client, "customer01")
    items, _ = _by_ref(client, headers)
    acc = client.get(f"/api/v1/accounts/{items['ACC-1001']['id']}", headers=headers)
    assert acc.status_code == 200
    body = acc.json()
    assert body["creditLimit"] == "10000.00"
    assert body["availableCredit"] == "5137.65"
    assert body["currentBalance"] == "4862.35"
    assert body["lastStatementBalance"] == "4701.10"
    assert body["minimumPayment"] == "121.56"
    assert body["standardPurchaseApr"] == "22.9"
    assert body["nextStatementDate"] == "2026-12-05"
    assert body["paymentDueDate"] == "2026-12-30"
    assert body["accountStatus"] == "Open" and body["openedOn"] == "2021-03-18"
    assert body["freshness"]["state"] == "freshness unavailable"
    assert body["informationalNotice"]


def test_absent_fields_are_null_not_zero(seeded, client):
    items, _ = _by_ref(client, login(client, "customer01"))
    sparse = items["ACC-1003"]
    for key in ("availableCredit", "currentBalance", "lastStatementBalance", "minimumPayment",
                "standardPurchaseApr", "nextStatementDate", "paymentDueDate"):
        assert sparse[key] is None
    assert items["ACC-1002"]["currentBalance"] == "0.00"


def test_pagination(seeded, client):
    headers = login(client, "customer01")
    page = client.get("/api/v1/accounts?limit=2&offset=2", headers=headers).json()
    assert len(page["items"]) == 1 and page["total"] == 3
    assert client.get("/api/v1/accounts?limit=0", headers=headers).status_code == 422


def test_foreign_account_is_404_and_bad_id_422(seeded, client, db_session):
    foreign = db_session.scalar(select(Account).where(Account.source_ref == "ACC-2001"))
    headers = login(client, "customer01")
    assert client.get(f"/api/v1/accounts/{foreign.id}", headers=headers).status_code == 404
    assert client.get("/api/v1/accounts/not-a-uuid", headers=headers).status_code == 422
    own = client.get("/api/v1/accounts", headers=login(client, "customer02")).json()
    assert [i["sourceRef"] for i in own["items"]] == ["ACC-2001"]


def test_accounts_need_auth(seeded, client):
    assert client.get("/api/v1/accounts").status_code == 401


def test_seed_is_idempotent(seeded, db_session):
    from app.seed import seed_database

    seed_database(db_session)
    db_session.commit()
    assert len(db_session.scalars(select(Account)).all()) == 4

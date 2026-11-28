from __future__ import annotations

from sqlalchemy import select, update

from app.models import Account, AppSetting, Transaction
from tests.conftest import login
from tests.factories import make_account, make_customer, make_transaction


def _txn(db, ref):
    return db.scalar(select(Transaction).where(Transaction.source_ref == ref))


def test_detail_all_fields_pending_no_posted_date(seeded, client, db_session):
    t = _txn(db_session, "TXN-1")
    r = client.get(f"/api/v1/transactions/{t.id}", headers=login(client, "customer01"))
    assert r.status_code == 200
    b = r.json()
    assert b["id"] == str(t.id) and b["transactionStatus"] == "Pending"
    assert b["postedDate"] is None and b["transactionTime"]
    assert b["transactionAmount"] == "42.15" and b["maskedPan"] == "**** 4821"
    assert b["merchantName"] and b["merchantCategoryCode"]
    assert "eligibleForInstalment" in b
    assert b["freshness"]["state"] == "unconfirmed freshness"
    assert b["freshness"]["sourceTime"]


def test_detail_posted_has_both_dates(seeded, client, db_session):
    t = _txn(db_session, "TXN-3")
    b = client.get(f"/api/v1/transactions/{t.id}", headers=login(client, "customer01")).json()
    assert b["postedDate"] == "2026-11-21" and b["transactionTime"]


def test_instalment_indicator_is_source_flag(seeded, client, db_session):
    t = _txn(db_session, "TXN-4")
    b = client.get(f"/api/v1/transactions/{t.id}", headers=login(client, "customer01")).json()
    assert b["eligibleForInstalment"] is True


def test_freshness_stale_with_max_age(seeded, client, db_session):
    t = _txn(db_session, "TXN-1")
    db_session.execute(
        update(AppSetting)
        .where(AppSetting.setting_key == "freshness.max_age_seconds.transaction")
        .values(value_text="300", approval_status="approved")
    )
    db_session.commit()
    h = login(client, "customer01")
    assert client.get(f"/api/v1/transactions/{t.id}", headers=h).json()["freshness"]["state"] == "stale"
    items = client.get(f"/api/v1/accounts/{t.account_id}/transactions", headers=h).json()["items"]
    assert {i["freshness"]["state"] for i in items} == {"stale"}


def test_foreign_transaction_404(seeded, client, db_session):
    other = make_account(db_session, make_customer(db_session))
    t = make_transaction(db_session, other)
    h = login(client, "customer01")
    r = client.get(f"/api/v1/transactions/{t.id}", headers=h)
    assert r.status_code == 404 and set(r.json()) == {"detail"}
    assert db_session.get(Account, other.id) is not None


def test_unknown_id_404_malformed_422(seeded, client):
    h = login(client, "customer01")
    assert client.get("/api/v1/transactions/00000000-0000-0000-0000-0000000000aa", headers=h).status_code == 404
    assert client.get("/api/v1/transactions/not-a-uuid", headers=h).status_code == 422


def test_auth_required_and_admin_forbidden(seeded, client, db_session):
    t = _txn(db_session, "TXN-1")
    assert client.get(f"/api/v1/transactions/{t.id}").status_code == 401
    r = client.get(f"/api/v1/transactions/{t.id}", headers=login(client, "admin01"))
    assert r.status_code == 403


def test_no_write_methods(seeded, client, db_session):
    t = _txn(db_session, "TXN-1")
    h = login(client, "customer01")
    assert client.post(f"/api/v1/transactions/{t.id}", headers=h).status_code in (404, 405)
    assert client.delete(f"/api/v1/transactions/{t.id}", headers=h).status_code in (404, 405)

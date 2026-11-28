from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.models import Account
from tests.conftest import login
from tests.factories import make_payment


def _acc(db, ref):
    return db.scalar(select(Account).where(Account.source_ref == ref))


def _url(db, ref="ACC-1001", q=""):
    return f"/api/v1/accounts/{_acc(db, ref).id}/payments{q}"


def test_seeded_list_fields_masked_and_ordered(seeded, client, db_session):
    r = client.get(_url(db_session), headers=login(client, "customer01"))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 6 and body["offset"] == 0
    dates = [i["paymentDate"] for i in body["items"]]
    assert dates == sorted(dates, reverse=True) and dates[0] == "2026-12-15"
    first = body["items"][0]
    assert first["paymentStatus"] == "Submitted" and first["paymentType"] == "Scheduled"
    assert first["paymentAmount"] == "300.00" and first["paymentMethod"] == "FasterPayments"
    assert first["sourceBankName"] == "Nationwide Current Account"
    assert first["freshness"]["state"] == "freshness unavailable"
    assert first["informationalNotice"]
    for item in body["items"]:
        assert item["sourceMaskedAccount"].startswith("****")
    by_ref = {i["sourceRef"]: i for i in body["items"]}
    assert by_ref["PMT-6"]["viaMandateRef"] == "MND-1" and by_ref["PMT-1"]["viaMandateRef"] is None
    assert {i["paymentStatus"] for i in body["items"]} == {
        "Completed", "Processing", "Failed", "Submitted", "Cancelled"
    }


def test_filters(seeded, client, db_session):
    h = login(client, "customer01")
    r = client.get(_url(db_session, q="?paymentType=Scheduled"), headers=h).json()
    assert r["total"] == 2 and {i["paymentType"] for i in r["items"]} == {"Scheduled"}
    r = client.get(_url(db_session, q="?paymentStatus=Completed"), headers=h).json()
    assert r["total"] == 2
    r = client.get(_url(db_session, q="?paymentType=OneOff&paymentStatus=Failed"), headers=h).json()
    assert r["total"] == 1 and r["items"][0]["sourceRef"] == "PMT-3"
    assert client.get(_url(db_session, q="?paymentStatus=Settled"), headers=h).status_code == 422
    assert client.get(_url(db_session, q="?paymentType=Bogus"), headers=h).status_code == 422


def test_paging(seeded, client, db_session):
    h = login(client, "customer01")
    page = client.get(_url(db_session, q="?limit=2&offset=4"), headers=h).json()
    assert len(page["items"]) == 2 and page["total"] == 6 and page["limit"] == 2 and page["offset"] == 4
    assert client.get(_url(db_session, q="?offset=10"), headers=h).json()["items"] == []
    for q in ("?limit=0", "?limit=101", "?offset=-1"):
        assert client.get(_url(db_session, q=q), headers=h).status_code == 422


def test_id_tiebreak_same_date(seeded, client, db_session):
    acc = _acc(db_session, "ACC-1002")
    rows = [make_payment(db_session, acc, payment_date=date(2026, 5, 1)) for _ in range(3)]
    r = client.get(_url(db_session, "ACC-1002"), headers=login(client, "customer01")).json()
    assert [i["id"] for i in r["items"]] == sorted((str(x.id) for x in rows), reverse=True)


def test_empty_page(seeded, client, db_session):
    r = client.get(_url(db_session, "ACC-1002"), headers=login(client, "customer01"))
    assert r.status_code == 200
    assert r.json()["items"] == [] and r.json()["total"] == 0


def test_null_source_account_allowed(seeded, client, db_session):
    acc = _acc(db_session, "ACC-1002")
    make_payment(db_session, acc, source_masked_account=None)
    items = client.get(_url(db_session, "ACC-1002"), headers=login(client, "customer01")).json()["items"]
    assert items[0]["sourceMaskedAccount"] is None


def test_auth_ownership_and_validation(seeded, client, db_session):
    assert client.get(_url(db_session)).status_code == 401
    assert client.get(_url(db_session), headers=login(client, "customer02")).status_code == 404
    assert client.get(_url(db_session), headers=login(client, "admin01")).status_code == 403
    h = login(client, "customer01")
    assert client.get("/api/v1/accounts/not-a-uuid/payments", headers=h).status_code == 422


def test_no_write_methods(seeded, client, db_session):
    h = login(client, "customer01")
    for method in ("post", "put", "patch", "delete"):
        r = getattr(client, method)(_url(db_session), headers=h)
        assert r.status_code in (404, 405)

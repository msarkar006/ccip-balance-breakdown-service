from __future__ import annotations

from sqlalchemy import select

from app.models import Payment
from app.policy import InformationOnlyPolicy
from tests.conftest import login
from tests.factories import make_account, make_customer, make_payment


def _pmt(db, ref):
    return db.scalar(select(Payment).where(Payment.source_ref == ref))


def test_detail_lifecycle_verbatim_and_notice(seeded, client, db_session):
    h = login(client, "customer01")
    for ref, status, ptype in [
        ("PMT-1", "Completed", "OneOff"),
        ("PMT-2", "Processing", "OneOff"),
        ("PMT-3", "Failed", "OneOff"),
        ("PMT-4", "Submitted", "Scheduled"),
        ("PMT-5", "Cancelled", "Scheduled"),
    ]:
        p = _pmt(db_session, ref)
        r = client.get(f"/api/v1/payments/{p.id}", headers=h)
        assert r.status_code == 200
        b = r.json()
        assert b["paymentStatus"] == status and b["paymentType"] == ptype
        assert b["informationalNotice"] == InformationOnlyPolicy.PAYMENT_NOTICE
        assert b["freshness"]["state"] == "freshness unavailable"
        assert b["sourceMaskedAccount"].startswith("****")


def test_mandate_reference_kept(seeded, client, db_session):
    p = _pmt(db_session, "PMT-6")
    b = client.get(f"/api/v1/payments/{p.id}", headers=login(client, "customer01")).json()
    assert b["viaMandateRef"] == "MND-1" and b["paymentType"] == "DirectDebitCollection"


def test_foreign_unknown_malformed_and_auth(seeded, client, db_session):
    other = make_payment(db_session, make_account(db_session, make_customer(db_session)))
    h = login(client, "customer01")
    r = client.get(f"/api/v1/payments/{other.id}", headers=h)
    assert r.status_code == 404 and set(r.json()) == {"detail"}
    assert client.get("/api/v1/payments/00000000-0000-0000-0000-0000000000aa", headers=h).status_code == 404
    assert client.get("/api/v1/payments/not-a-uuid", headers=h).status_code == 422
    p = _pmt(db_session, "PMT-1")
    assert client.get(f"/api/v1/payments/{p.id}").status_code == 401
    assert client.get(f"/api/v1/payments/{p.id}", headers=login(client, "admin01")).status_code == 403

from __future__ import annotations

import re

import pytest
from sqlalchemy import select

from app.models import Account, Payment
from tests.conftest import login

_ID = "00000000-0000-0000-0000-000000000001"
_PATHS = [
    "/api/v1/payments",
    f"/api/v1/payments/{_ID}",
    f"/api/v1/accounts/{_ID}/payments",
    "/api/v1/transfers",
    f"/api/v1/transfers/{_ID}",
    "/api/v1/payees",
    f"/api/v1/payees/{_ID}",
    "/api/v1/mandates",
    f"/api/v1/mandates/{_ID}",
]


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("path", _PATHS)
def test_write_methods_get_safe_404(seeded, client, method, path):
    h = login(client, "customer01")
    for headers in (h, {}):
        r = client.request(method, path, headers=headers, json={"amount": "1.00"})
        assert r.status_code == 404, (method, path)
        assert r.json() == {"detail": "Resource not found"}
        assert "allow" not in {k.lower() for k in r.headers}


@pytest.mark.parametrize("path", ["/api/v1/transfers", "/api/v1/payees", "/api/v1/mandates"])
def test_deferred_domains_not_routed(seeded, client, path):
    assert client.get(path, headers=login(client, "customer01")).status_code == 404


def test_no_full_identifiers_in_payment_responses(seeded, client, db_session):
    h = login(client, "customer01")
    acc = db_session.scalar(select(Account).where(Account.source_ref == "ACC-1001"))
    page = client.get(f"/api/v1/accounts/{acc.id}/payments", headers=h).json()
    texts = [client.get(f"/api/v1/payments/{p.id}", headers=h).text for p in db_session.scalars(select(Payment))
             if p.account_id == acc.id]
    texts.append(str(page))
    assert len(texts) == 7
    for t in texts:
        assert not re.search(r"\b\d{12,19}\b", t)
        assert not re.search(r"\b\d{2}-\d{2}-\d{2}\b", t)


def test_payment_response_has_no_control_fields(seeded, client, db_session):
    p = db_session.scalars(select(Payment)).first()
    b = client.get(f"/api/v1/payments/{p.id}", headers=login(client, "customer01"))
    if b.status_code == 200:
        keys = " ".join(b.json()).lower()
        for word in ("cancel", "retry", "amend", "action", "link", "href"):
            assert word not in keys

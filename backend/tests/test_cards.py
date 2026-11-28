from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models import Account
from tests.conftest import login


def _account_id(db_session, ref: str) -> uuid.UUID:
    return db_session.scalar(select(Account.id).where(Account.source_ref == ref))


def test_cards_masked_and_status_verbatim(seeded, client, db_session):
    headers = login(client, "customer01")
    r = client.get(f"/api/v1/accounts/{_account_id(db_session, 'ACC-1001')}/cards", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    card = body["items"][0]
    assert card["maskedPan"] == "**** 4821"
    assert card["cardStatus"] == "Active"
    assert card["expiryMonthYear"] == "2028-09"
    assert card["isDigital"] is False


def test_pending_activation_status_retained(seeded, client, db_session):
    headers = login(client, "customer01")
    r = client.get(f"/api/v1/accounts/{_account_id(db_session, 'ACC-1003')}/cards", headers=headers)
    card = r.json()["items"][0]
    assert card["maskedPan"] == "**** 9040"
    assert card["cardStatus"] == "PendingActivation"


def test_foreign_account_is_404(seeded, client, db_session):
    headers = login(client, "customer01")
    r = client.get(f"/api/v1/accounts/{_account_id(db_session, 'ACC-2001')}/cards", headers=headers)
    assert r.status_code == 404


def test_unauthenticated_and_bad_id(seeded, client):
    assert client.get(f"/api/v1/accounts/{uuid.uuid4()}/cards").status_code == 401
    headers = login(client, "customer01")
    assert client.get("/api/v1/accounts/not-a-uuid/cards", headers=headers).status_code == 422


def test_unmasked_value_rejected():
    import pytest

    from app.exceptions import MaskingViolationError
    from app.utils import mask_check

    with pytest.raises(MaskingViolationError):
        mask_check("4111111111114821")

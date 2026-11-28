from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.models import Account, BalanceBreakdown
from tests.conftest import login
from tests.factories import make_breakdown, make_category


def _account(db_session, ref: str) -> Account:
    return db_session.scalar(select(Account).where(Account.source_ref == ref))


def _breakdown_id(db_session, ref: str) -> uuid.UUID:
    return db_session.scalar(select(BalanceBreakdown.id).where(BalanceBreakdown.source_ref == ref))


def test_detail_shows_as_of_totals_and_ranked_categories(seeded, client, db_session):
    headers = login(client, "customer01")
    r = client.get(f"/api/v1/balance-breakdowns/{_breakdown_id(db_session, 'BBD-1')}", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["asOf"].startswith("2026-11-24T08:15:00")
    assert body["totalOutstanding"] == "4862.35"
    assert body["pendingTotal"] == "114.20"
    assert body["purchasesSubtotal"] == "1852.10"
    assert body["balanceTransfersSubtotal"] == "3010.25"
    assert body["freshness"]["state"] == "unconfirmed freshness"
    assert body["notice"]
    cats = body["categories"]
    assert [c["displayRank"] for c in cats] == [1, 2, 3, 4, 5]
    assert cats[2]["categoryLabel"] == "Balance transfer 1"
    assert cats[2]["categoryBalance"] == "1800.00"
    assert cats[2]["sourceBalanceTransferRef"] == "BT-1"
    assert cats[4]["sourceInstalmentPlanRef"] == "IP-66"


def test_categories_ordered_by_rank_not_insertion(seeded, client, db_session):
    account = _account(db_session, "ACC-1001")
    bd = make_breakdown(db_session, account, source_ref="BBD-T1")
    make_category(db_session, bd, display_rank=3, category_label="third")
    make_category(db_session, bd, display_rank=1, category_label="first")
    make_category(db_session, bd, display_rank=2, category_label="second")
    headers = login(client, "customer01")
    r = client.get(f"/api/v1/balance-breakdowns/{bd.id}", headers=headers)
    assert [c["categoryLabel"] for c in r.json()["categories"]] == ["first", "second", "third"]


def test_pending_not_relabelled_for_zero_balance(seeded, client, db_session):
    headers = login(client, "customer01")
    r = client.get(f"/api/v1/balance-breakdowns/{_breakdown_id(db_session, 'BBD-2')}", headers=headers)
    body = r.json()
    assert body["isZeroBalance"] is True
    assert body["totalOutstanding"] == "0.00"
    assert body["pendingTotal"] == "4.80"
    assert "posted" not in body and "settledTotal" not in body


def test_list_orders_as_of_desc_null_last(seeded, client, db_session):
    account = _account(db_session, "ACC-1001")
    make_breakdown(db_session, account, source_ref="BBD-NULL", as_of=None)
    make_breakdown(db_session, account, source_ref="BBD-OLD", as_of=datetime(2026, 1, 1, tzinfo=UTC))
    headers = login(client, "customer01")
    r = client.get(f"/api/v1/accounts/{account.id}/balance-breakdowns", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert [i["sourceRef"] for i in body["items"]] == ["BBD-1", "BBD-OLD", "BBD-NULL"]
    assert body["total"] == 3
    assert body["items"][-1]["asOf"] is None
    assert body["items"][-1]["freshness"]["state"] == "freshness unavailable"


def test_missing_as_of_is_never_replaced_by_now(seeded, client, db_session):
    headers = login(client, "customer01")
    r = client.get(f"/api/v1/balance-breakdowns/{_breakdown_id(db_session, 'BBD-3')}", headers=headers)
    body = r.json()
    assert body["asOf"] is None
    assert body["freshness"]["state"] == "freshness unavailable"


def test_foreign_ids_are_404(seeded, client, db_session):
    headers = login(client, "customer02")
    bid = _breakdown_id(db_session, "BBD-1")
    assert client.get(f"/api/v1/balance-breakdowns/{bid}", headers=headers).status_code == 404
    acc = _account(db_session, "ACC-1001")
    assert client.get(f"/api/v1/accounts/{acc.id}/balance-breakdowns", headers=headers).status_code == 404
    assert client.get(f"/api/v1/balance-breakdowns/{uuid.uuid4()}", headers=headers).status_code == 404


def test_auth_and_validation(seeded, client, db_session):
    acc = _account(db_session, "ACC-1001")
    assert client.get(f"/api/v1/accounts/{acc.id}/balance-breakdowns").status_code == 401
    headers = login(client, "customer01")
    base = f"/api/v1/accounts/{acc.id}/balance-breakdowns"
    for q in ("limit=0", "limit=101", "offset=-1", "limit=abc"):
        assert client.get(f"{base}?{q}", headers=headers).status_code == 422
    assert client.get("/api/v1/balance-breakdowns/not-a-uuid", headers=headers).status_code == 422


def test_administrator_forbidden(seeded, client, db_session):
    headers = login(client, "admin01")
    r = client.get(f"/api/v1/balance-breakdowns/{_breakdown_id(db_session, 'BBD-1')}", headers=headers)
    assert r.status_code == 403


def test_qualifiers_stay_on_their_category_with_notice(seeded, client, db_session):
    headers = login(client, "customer01")
    body = client.get(f"/api/v1/balance-breakdowns/{_breakdown_id(db_session, 'BBD-1')}", headers=headers).json()
    cats = {c["sourceRef"]: c for c in body["categories"]}
    assert cats["CAT-2"]["promoEndDate"] == "2027-03-14" and cats["CAT-2"]["revertRatePercent"] == "22.9"
    assert cats["CAT-3"]["promoEndDate"] == "2027-06-30"
    assert cats["CAT-1"]["promoEndDate"] is None and cats["CAT-1"]["revertRatePercent"] is None
    for c in body["categories"]:
        assert c["qualifierNotice"]
        low = c["qualifierNotice"].lower()
        assert "not a pricing promise" in low and "guarantee" not in low

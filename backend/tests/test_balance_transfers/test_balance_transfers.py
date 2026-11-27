"""
Test balance transfer tracking endpoints.
"""
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.balance_breakdown import BalanceBreakdown
from app.models.balance_category import BalanceCategory
from app.models.balance_transfer import BalanceTransfer
from app.models.credit_card_account import CreditCardAccount
from app.models.tracking_event import TrackingEvent


def test_get_balance_transfers_success(auth_client, db_session):
    """Test retrieving balance transfer history."""
    # Create account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****1001",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=15),
    )
    db_session.add(account)
    db_session.commit()

    # Create balance transfers with explicit created_at ordering
    bt1 = BalanceTransfer(
        account_id=account.id,
        external_transfer_id="BT-TEST-1",
        transfer_amount=Decimal("1000.00"),
        promotional_rate=Decimal("0.00"),
        promotional_period_months=12,
        status="Completed",
        processed_at=datetime.now() - timedelta(days=30),
    )
    db_session.add(bt1)
    db_session.commit()

    bt2 = BalanceTransfer(
        account_id=account.id,
        external_transfer_id="BT-TEST-2",
        transfer_amount=Decimal("1500.00"),
        promotional_rate=Decimal("0.00"),
        promotional_period_months=18,
        status="Submitted",
        processed_at=None,
    )
    db_session.add(bt2)
    db_session.commit()

    # Test endpoint
    response = auth_client.get(f"/api/v1/balance-transfers?account_id={account.id}")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "has_more" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Verify both items are present (order may vary due to timestamp resolution)
    ids = {item["external_transfer_id"] for item in data["items"]}
    assert "BT-TEST-1" in ids
    assert "BT-TEST-2" in ids


def test_get_balance_transfer_detail_success(auth_client, db_session):
    """Test retrieving balance transfer detail with timeline."""
    # Create account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****1001",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=15),
    )
    db_session.add(account)
    db_session.commit()

    # Create balance transfer
    bt = BalanceTransfer(
        account_id=account.id,
        external_transfer_id="BT-TEST-DETAIL",
        transfer_amount=Decimal("1000.00"),
        promotional_rate=Decimal("0.00"),
        promotional_period_months=12,
        status="Completed",
        processed_at=datetime.now() - timedelta(days=30),
    )
    db_session.add(bt)
    db_session.commit()

    # Create tracking events
    event1 = TrackingEvent(
        entity_type="BalanceTransfer",
        entity_id=str(bt.id),
        event_type="submitted",
        status="Submitted",
        event_data="Balance transfer submitted",
        occurred_at=datetime.now() - timedelta(days=32),
    )
    event2 = TrackingEvent(
        entity_type="BalanceTransfer",
        entity_id=str(bt.id),
        event_type="completed",
        status="Completed",
        event_data="Balance transfer completed",
        occurred_at=datetime.now() - timedelta(days=30),
    )
    db_session.add(event1)
    db_session.add(event2)
    db_session.commit()

    # Test endpoint
    response = auth_client.get(f"/api/v1/balance-transfers/{bt.id}?account_id={account.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == bt.id
    assert data["external_transfer_id"] == "BT-TEST-DETAIL"
    assert data["status"] == "Completed"
    assert "timeline" in data
    assert len(data["timeline"]) == 2
    assert data["timeline"][0]["event_type"] == "submitted"
    assert data["timeline"][1]["event_type"] == "completed"


def test_get_balance_transfer_detail_with_promotional_context(auth_client, db_session):
    """Test balance transfer detail includes promotional context."""
    # Create account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****1001",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=15),
    )
    db_session.add(account)
    db_session.commit()

    # Create balance transfer with promo
    processed_at = datetime.now() - timedelta(days=30)
    bt = BalanceTransfer(
        account_id=account.id,
        external_transfer_id="BT-PROMO",
        transfer_amount=Decimal("1000.00"),
        promotional_rate=Decimal("0.00"),
        promotional_period_months=12,
        status="Completed",
        processed_at=processed_at,
    )
    db_session.add(bt)
    db_session.commit()

    # Test endpoint
    response = auth_client.get(f"/api/v1/balance-transfers/{bt.id}?account_id={account.id}")
    assert response.status_code == 200
    data = response.json()

    assert "promotional_context" in data
    assert data["promotional_context"] is not None
    assert data["promotional_context"]["promo_rate"] == "0.00"
    assert "promo_start_date" in data["promotional_context"]
    assert "promo_end_date" in data["promotional_context"]


def test_get_balance_transfer_detail_with_linked_category(auth_client, db_session):
    """Test balance transfer detail includes linked category via source_link."""
    # Create account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****1001",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=15),
    )
    db_session.add(account)
    db_session.commit()

    # Create balance transfer
    bt = BalanceTransfer(
        account_id=account.id,
        external_transfer_id="BT-LINKED",
        transfer_amount=Decimal("500.00"),
        promotional_rate=Decimal("0.00"),
        promotional_period_months=12,
        status="Completed",
        processed_at=datetime.now() - timedelta(days=30),
    )
    db_session.add(bt)
    db_session.commit()

    # Create balance breakdown and category linked to this transfer
    breakdown = BalanceBreakdown(
        account_id=account.id,
        total_balance=Decimal("500.00"),
        snapshot_date=datetime.now(),
    )
    db_session.add(breakdown)
    db_session.commit()

    category = BalanceCategory(
        breakdown_id=breakdown.id,
        category_name="BalanceTransfer",
        category_amount=Decimal("500.00"),
        apr=Decimal("0.00"),
        source_balance_transfer_id=bt.id,
    )
    db_session.add(category)
    db_session.commit()

    # Test endpoint
    response = auth_client.get(f"/api/v1/balance-transfers/{bt.id}?account_id={account.id}")
    assert response.status_code == 200
    data = response.json()

    assert "source_link" in data
    assert data["source_link"] is not None
    assert data["source_link"]["source_type"] == "BalanceTransfer"
    assert data["source_link"]["source_id"] == bt.id
    assert data["source_link"]["category_id"] == category.id
    assert data["source_link"]["category_name"] == "BalanceTransfer"


def test_get_balance_transfer_detail_rejected_guidance(auth_client, db_session):
    """Test balance transfer detail includes guidance for Rejected status."""
    # Create account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****1001",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=15),
    )
    db_session.add(account)
    db_session.commit()

    # Create rejected balance transfer
    bt = BalanceTransfer(
        account_id=account.id,
        external_transfer_id="BT-REJECTED",
        transfer_amount=Decimal("2000.00"),
        promotional_rate=None,
        promotional_period_months=None,
        status="Rejected",
        processed_at=datetime.now() - timedelta(days=1),
    )
    db_session.add(bt)
    db_session.commit()

    # Test endpoint
    response = auth_client.get(f"/api/v1/balance-transfers/{bt.id}?account_id={account.id}")
    assert response.status_code == 200
    data = response.json()

    assert "guidance" in data
    assert data["guidance"] is not None
    assert data["guidance"]["message_code"] == "BT_REJECTED"
    assert "rejected" in data["guidance"]["message"].lower()
    assert data["guidance"]["next_step"] is not None


def test_get_balance_transfer_detail_not_found(auth_client, db_session):
    """Test retrieving non-existent balance transfer returns 404."""
    response = auth_client.get("/api/v1/balance-transfers/999999?account_id=1")
    assert response.status_code == 404


def test_get_balance_transfers_pagination(auth_client, db_session):
    """Test balance transfer history pagination."""
    # Create account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****1001",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=15),
    )
    db_session.add(account)
    db_session.commit()

    # Create 15 balance transfers
    for i in range(15):
        bt = BalanceTransfer(
            account_id=account.id,
            external_transfer_id=f"BT-PAGE-{i+1}",
            transfer_amount=Decimal("100.00"),
            promotional_rate=Decimal("0.00"),
            promotional_period_months=12,
            status="Completed",
            processed_at=datetime.now() - timedelta(days=i),
        )
        db_session.add(bt)
    db_session.commit()

    # Test first page
    response = auth_client.get(f"/api/v1/balance-transfers?account_id={account.id}&limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 15
    assert data["has_more"] is True

    # Test second page
    response = auth_client.get(f"/api/v1/balance-transfers?account_id={account.id}&limit=10&offset=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["total"] == 15
    assert data["has_more"] is False


def test_get_balance_transfers_requires_auth(client, db_session):
    """Test that balance transfers endpoint requires authentication."""
    response = client.get("/api/v1/balance-transfers?account_id=1")
    assert response.status_code == 401

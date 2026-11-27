"""
Test money transfer tracking endpoints.
"""
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.credit_card_account import CreditCardAccount
from app.models.money_transfer import MoneyTransfer
from app.models.payee import Payee
from app.models.tracking_event import TrackingEvent


def test_get_money_transfers_success(auth_client, db_session):
    """Test retrieving money transfer history."""
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

    # Create payee
    payee = Payee(
        account_id=account.id,
        payee_name="John Smith",
        account_number_masked="****1234",
        sort_code_masked="12-34-56",
        is_active=True,
    )
    db_session.add(payee)
    db_session.commit()

    # Create money transfers
    mt1 = MoneyTransfer(
        account_id=account.id,
        payee_id=payee.id,
        external_transfer_id="MT-TEST-1",
        amount=Decimal("100.00"),
        currency="GBP",
        status="Completed",
        processed_at=datetime.now() - timedelta(days=5),
    )
    mt2 = MoneyTransfer(
        account_id=account.id,
        payee_id=payee.id,
        external_transfer_id="MT-TEST-2",
        amount=Decimal("250.00"),
        currency="GBP",
        status="Submitted",
        processed_at=None,
    )
    db_session.add(mt1)
    db_session.add(mt2)
    db_session.commit()

    # Test endpoint
    response = auth_client.get(f"/api/v1/money-transfers?account_id={account.id}")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "has_more" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Verify both items are present (order may vary due to timestamp resolution)
    ids = {item["external_transfer_id"] for item in data["items"]}
    assert "MT-TEST-1" in ids
    assert "MT-TEST-2" in ids
    # Verify payee name is included
    assert all(item["payee_name"] == "John Smith" for item in data["items"])


def test_get_money_transfer_detail_success(auth_client, db_session):
    """Test retrieving money transfer detail with timeline and payee info."""
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

    # Create payee
    payee = Payee(
        account_id=account.id,
        payee_name="Jane Doe",
        account_number_masked="****5678",
        sort_code_masked="98-76-54",
        is_active=True,
    )
    db_session.add(payee)
    db_session.commit()

    # Create money transfer
    mt = MoneyTransfer(
        account_id=account.id,
        payee_id=payee.id,
        external_transfer_id="MT-TEST-DETAIL",
        amount=Decimal("150.00"),
        currency="GBP",
        status="Completed",
        processed_at=datetime.now() - timedelta(days=3),
    )
    db_session.add(mt)
    db_session.commit()

    # Create tracking events
    event1 = TrackingEvent(
        entity_type="MoneyTransfer",
        entity_id=str(mt.id),
        event_type="submitted",
        status="Submitted",
        event_data="Money transfer submitted",
        occurred_at=datetime.now() - timedelta(days=4),
    )
    event2 = TrackingEvent(
        entity_type="MoneyTransfer",
        entity_id=str(mt.id),
        event_type="completed",
        status="Completed",
        event_data="Money transfer completed",
        occurred_at=datetime.now() - timedelta(days=3),
    )
    db_session.add(event1)
    db_session.add(event2)
    db_session.commit()

    # Test endpoint
    response = auth_client.get(f"/api/v1/money-transfers/{mt.id}?account_id={account.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == mt.id
    assert data["external_transfer_id"] == "MT-TEST-DETAIL"
    assert data["status"] == "Completed"
    assert data["payee"]["payee_name"] == "Jane Doe"
    assert data["payee"]["account_number_masked"] == "****5678"
    assert "timeline" in data
    assert len(data["timeline"]) == 2
    assert data["timeline"][0]["event_type"] == "submitted"
    assert data["timeline"][1]["event_type"] == "completed"


def test_get_money_transfer_detail_failed_guidance(auth_client, db_session):
    """Test money transfer detail includes guidance for Failed status."""
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

    # Create payee
    payee = Payee(
        account_id=account.id,
        payee_name="ACME Corp",
        account_number_masked="****9012",
        sort_code_masked="11-22-33",
        is_active=True,
    )
    db_session.add(payee)
    db_session.commit()

    # Create failed money transfer
    mt = MoneyTransfer(
        account_id=account.id,
        payee_id=payee.id,
        external_transfer_id="MT-FAILED",
        amount=Decimal("500.00"),
        currency="GBP",
        status="Failed",
        processed_at=datetime.now() - timedelta(hours=12),
    )
    db_session.add(mt)
    db_session.commit()

    # Test endpoint
    response = auth_client.get(f"/api/v1/money-transfers/{mt.id}?account_id={account.id}")
    assert response.status_code == 200
    data = response.json()

    assert "guidance" in data
    assert data["guidance"] is not None
    assert data["guidance"]["message_code"] == "MT_FAILED"
    assert "failed" in data["guidance"]["message"].lower()
    assert data["guidance"]["next_step"] is not None


def test_get_money_transfer_detail_blocked_guidance(auth_client, db_session):
    """Test money transfer detail includes guidance for Blocked status."""
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

    # Create payee
    payee = Payee(
        account_id=account.id,
        payee_name="Suspect Entity",
        account_number_masked="****0000",
        sort_code_masked="00-00-00",
        is_active=True,
    )
    db_session.add(payee)
    db_session.commit()

    # Create blocked money transfer
    mt = MoneyTransfer(
        account_id=account.id,
        payee_id=payee.id,
        external_transfer_id="MT-BLOCKED",
        amount=Decimal("1000.00"),
        currency="GBP",
        status="Blocked",
        processed_at=datetime.now() - timedelta(hours=6),
    )
    db_session.add(mt)
    db_session.commit()

    # Test endpoint
    response = auth_client.get(f"/api/v1/money-transfers/{mt.id}?account_id={account.id}")
    assert response.status_code == 200
    data = response.json()

    assert "guidance" in data
    assert data["guidance"] is not None
    assert data["guidance"]["message_code"] == "MT_BLOCKED"
    assert "blocked" in data["guidance"]["message"].lower()
    assert "security" in data["guidance"]["message"].lower()


def test_get_money_transfer_detail_not_found(auth_client, db_session):
    """Test retrieving non-existent money transfer returns 404."""
    response = auth_client.get("/api/v1/money-transfers/999999?account_id=1")
    assert response.status_code == 404


def test_get_money_transfers_pagination(auth_client, db_session):
    """Test money transfer history pagination."""
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

    # Create payee
    payee = Payee(
        account_id=account.id,
        payee_name="Test Payee",
        account_number_masked="****1111",
        sort_code_masked="11-11-11",
        is_active=True,
    )
    db_session.add(payee)
    db_session.commit()

    # Create 15 money transfers
    for i in range(15):
        mt = MoneyTransfer(
            account_id=account.id,
            payee_id=payee.id,
            external_transfer_id=f"MT-PAGE-{i+1}",
            amount=Decimal("50.00"),
            currency="GBP",
            status="Completed",
            processed_at=datetime.now() - timedelta(days=i),
        )
        db_session.add(mt)
    db_session.commit()

    # Test first page
    response = auth_client.get(f"/api/v1/money-transfers?account_id={account.id}&limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 15
    assert data["has_more"] is True

    # Test second page
    response = auth_client.get(f"/api/v1/money-transfers?account_id={account.id}&limit=10&offset=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["total"] == 15
    assert data["has_more"] is False


def test_get_money_transfers_requires_auth(client, db_session):
    """Test that money transfers endpoint requires authentication."""
    response = client.get("/api/v1/money-transfers?account_id=1")
    assert response.status_code == 401

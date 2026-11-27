"""
Tests for payment endpoints - payment history and tracking.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.payment import Payment
from app.models.tracking_event import TrackingEvent


def test_get_payments_success(auth_client, db_session):
    """Test successful payment list retrieval."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    customer = Customer(
        external_customer_id="TEST-CUST-PMT",
        masked_name="Test C***",
        email="testpmt@example.com",
        phone_last_four="1111"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****9999",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=15)
    )
    db_session.add(account)
    db_session.flush()

    # Create test payments
    payments = [
        Payment(
            account_id=account.id,
            external_payment_id=f"PMT-TEST-{i}",
            payment_method="BankTransfer",
            amount=Decimal(f"{100 + i * 10}.00"),
            currency="GBP",
            status="Completed" if i <= 2 else "Processing",
            scheduled_date=datetime.now() + timedelta(days=i) if i > 2 else None,
            processed_at=datetime.now() - timedelta(days=i) if i <= 2 else None
        )
        for i in range(1, 6)
    ]
    for pmt in payments:
        db_session.add(pmt)
    db_session.commit()

    # Request payments
    response = auth_client.get(f"/api/v1/payments?account_id={account.id}&limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "has_more" in data
    assert data["total"] >= 5  # May include seed data
    assert len(data["items"]) >= 5
    assert data["has_more"] is False


def test_get_payment_detail_with_timeline(auth_client, db_session):
    """Test payment detail retrieval with tracking timeline."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    customer = Customer(
        external_customer_id="TEST-CUST-PMT-2",
        masked_name="Test C***",
        email="testpmt2@example.com",
        phone_last_four="2222"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****8888",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("3000.00"),
        available_credit=Decimal("2000.00"),
        current_balance=Decimal("1000.00"),
        minimum_payment_due=Decimal("50.00"),
        payment_due_date=datetime.now() + timedelta(days=10)
    )
    db_session.add(account)
    db_session.flush()

    # Create payment
    payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-DETAIL-TEST",
        payment_method="BankTransfer",
        amount=Decimal("150.00"),
        currency="GBP",
        status="Completed",
        scheduled_date=None,
        processed_at=datetime.now() - timedelta(days=1)
    )
    db_session.add(payment)
    db_session.flush()

    # Create tracking events
    events = [
        TrackingEvent(
            entity_type="Payment",
            entity_id=str(payment.id),
            event_type="submitted",
            status="Submitted",
            event_data="Payment submitted",
            occurred_at=datetime.now(timezone.utc) - timedelta(days=2)
        ),
        TrackingEvent(
            entity_type="Payment",
            entity_id=str(payment.id),
            event_type="processing",
            status="Processing",
            event_data="Payment processing",
            occurred_at=datetime.now(timezone.utc) - timedelta(days=1, hours=12)
        ),
        TrackingEvent(
            entity_type="Payment",
            entity_id=str(payment.id),
            event_type="completed",
            status="Completed",
            event_data="Payment completed",
            occurred_at=datetime.now(timezone.utc) - timedelta(days=1)
        ),
    ]
    for event in events:
        db_session.add(event)
    db_session.commit()

    response = auth_client.get(f"/api/v1/payments/{payment.id}")

    assert response.status_code == 200
    data = response.json()

    assert "payment" in data
    assert "timeline" in data
    assert "can_cancel" in data
    assert "cancellation_message" in data
    assert "guidance" in data

    assert data["payment"]["id"] == payment.id
    assert len(data["timeline"]) == 3
    assert data["can_cancel"] is False
    assert data["cancellation_message"] == "Payment already completed"

    # Verify timeline ordering (event_timestamp ASC)
    for i in range(len(data["timeline"]) - 1):
        current_ts = datetime.fromisoformat(data["timeline"][i]["event_timestamp"].replace("Z", "+00:00"))
        next_ts = datetime.fromisoformat(data["timeline"][i + 1]["event_timestamp"].replace("Z", "+00:00"))
        assert current_ts <= next_ts


def test_payment_can_cancel_logic(auth_client, db_session):
    """Test payment cancellation availability logic."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    customer = Customer(
        external_customer_id="TEST-CUST-PMT-3",
        masked_name="Test C***",
        email="testpmt3@example.com",
        phone_last_four="3333"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****7777",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("4000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("1000.00"),
        minimum_payment_due=Decimal("50.00"),
        payment_due_date=datetime.now() + timedelta(days=12)
    )
    db_session.add(account)
    db_session.flush()

    # Scheduled payment in future - can cancel
    future_payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-FUTURE",
        payment_method="BankTransfer",
        amount=Decimal("200.00"),
        currency="GBP",
        status="Submitted",
        scheduled_date=datetime.now(timezone.utc) + timedelta(days=5),
        processed_at=None
    )
    db_session.add(future_payment)
    db_session.flush()

    response = auth_client.get(f"/api/v1/payments/{future_payment.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["can_cancel"] is True
    assert data["cancellation_message"] is None

    # Completed payment - cannot cancel
    completed_payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-COMPLETED",
        payment_method="BankTransfer",
        amount=Decimal("150.00"),
        currency="GBP",
        status="Completed",
        scheduled_date=None,
        processed_at=datetime.now() - timedelta(days=1)
    )
    db_session.add(completed_payment)
    db_session.commit()

    response = auth_client.get(f"/api/v1/payments/{completed_payment.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["can_cancel"] is False
    assert "already completed" in data["cancellation_message"].lower()


def test_payment_guidance_messages(auth_client, db_session):
    """Test payment guidance for non-final/failed states."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    customer = Customer(
        external_customer_id="TEST-CUST-PMT-4",
        masked_name="Test C***",
        email="testpmt4@example.com",
        phone_last_four="4444"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****6666",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("2000.00"),
        available_credit=Decimal("1500.00"),
        current_balance=Decimal("500.00"),
        minimum_payment_due=Decimal("25.00"),
        payment_due_date=datetime.now() + timedelta(days=8)
    )
    db_session.add(account)
    db_session.flush()

    # Processing payment
    processing_payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-PROCESSING",
        payment_method="BankTransfer",
        amount=Decimal("100.00"),
        currency="GBP",
        status="Processing",
        scheduled_date=None,
        processed_at=None
    )
    db_session.add(processing_payment)
    db_session.flush()

    response = auth_client.get(f"/api/v1/payments/{processing_payment.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["guidance"] is not None
    assert data["guidance"]["message_code"] == "payment_processing"
    assert "processed" in data["guidance"]["message"].lower() or "processing" in data["guidance"]["message"].lower()

    # Failed payment
    failed_payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-FAILED",
        payment_method="DebitCard",
        amount=Decimal("75.00"),
        currency="GBP",
        status="Failed",
        scheduled_date=None,
        processed_at=datetime.now() - timedelta(hours=6)
    )
    db_session.add(failed_payment)
    db_session.flush()

    response = auth_client.get(f"/api/v1/payments/{failed_payment.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["guidance"] is not None
    assert data["guidance"]["message_code"] == "payment_failed"
    assert "failed" in data["guidance"]["message"].lower() or "could not" in data["guidance"]["message"].lower()

    # Restricted payment
    restricted_payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-RESTRICTED",
        payment_method="BankTransfer",
        amount=Decimal("500.00"),
        currency="GBP",
        status="Restricted",
        scheduled_date=datetime.now() + timedelta(days=10),
        processed_at=None
    )
    db_session.add(restricted_payment)
    db_session.commit()

    response = auth_client.get(f"/api/v1/payments/{restricted_payment.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["guidance"] is not None
    assert data["guidance"]["message_code"] == "payment_restricted"
    assert "review" in data["guidance"]["message"].lower() or "restricted" in data["guidance"]["message"].lower()


def test_get_payments_empty_state(auth_client, db_session):
    """Test empty state when no payments exist."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    customer = Customer(
        external_customer_id="TEST-CUST-PMT-5",
        masked_name="Test C***",
        email="testpmt5@example.com",
        phone_last_four="5555"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****5555",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("3000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("0.00"),
        minimum_payment_due=Decimal("0.00"),
        payment_due_date=datetime.now() + timedelta(days=20)
    )
    db_session.add(account)
    db_session.commit()

    response = auth_client.get(f"/api/v1/payments?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 0
    assert data["total"] == 0
    assert data["empty_state_message"] == "No payments found for this account"


def test_get_payment_not_found(auth_client, db_session):
    """Test payment detail for non-existent payment."""
    response = auth_client.get("/api/v1/payments/999999")
    assert response.status_code == 404


def test_get_payments_requires_auth(client, db_session):
    """Test that payments endpoint requires authentication."""
    response = client.get("/api/v1/payments?account_id=1")
    assert response.status_code == 401


def test_get_payment_detail_requires_auth(client, db_session):
    """Test that payment detail endpoint requires authentication."""
    response = client.get("/api/v1/payments/1")
    assert response.status_code == 401

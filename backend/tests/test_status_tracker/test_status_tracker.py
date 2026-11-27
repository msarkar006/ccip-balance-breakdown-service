"""
Tests for status tracker endpoints.
"""
from datetime import datetime, timedelta
from decimal import Decimal


def test_get_tracker_list_success(auth_client, db_session):
    """Test getting tracker list with mixed entities."""
    from app.models.balance_transfer import BalanceTransfer
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.money_transfer import MoneyTransfer
    from app.models.payee import Payee
    from app.models.payment import Payment
    from app.models.tracking_event import TrackingEvent

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-TRACK-1",
        masked_name="Test C***",
        email="track1@example.com",
        phone_last_four="1111"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****1111",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
    )
    db_session.add(account)
    db_session.flush()

    # Create payment (unresolved)
    payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-TRACK-1",
        payment_method="BankTransfer",
        amount=Decimal("100.00"),
        currency="GBP",
        status="Processing",
    )
    db_session.add(payment)
    db_session.flush()

    # Create tracking event for payment
    tracking_event = TrackingEvent(
        entity_type="Payment",
        entity_id=str(payment.id),
        event_type="processing",
        status="Processing",
        event_data="Payment processing",
        occurred_at=datetime.now(),
    )
    db_session.add(tracking_event)

    # Create money transfer (unresolved)
    payee = Payee(
        account_id=account.id,
        payee_name="Test Payee",
        account_number_masked="****9999",
        sort_code_masked="11-22-33",
        is_active=True,
    )
    db_session.add(payee)
    db_session.flush()

    mt = MoneyTransfer(
        account_id=account.id,
        payee_id=payee.id,
        external_transfer_id="MT-TRACK-1",
        amount=Decimal("200.00"),
        currency="GBP",
        status="Submitted",
    )
    db_session.add(mt)
    db_session.flush()

    # Create balance transfer (completed - should not appear in unresolved)
    bt = BalanceTransfer(
        account_id=account.id,
        external_transfer_id="BT-TRACK-1",
        transfer_amount=Decimal("500.00"),
        promotional_rate=Decimal("0.00"),
        promotional_period_months=12,
        status="Completed",
        processed_at=datetime.now(),
    )
    db_session.add(bt)

    db_session.commit()

    # Get tracker list (all)
    response = auth_client.get(
        "/api/v1/status-tracker",
        params={"account_id": account.id}
    )

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "unresolved_count" in data
    assert len(data["items"]) >= 2  # At least payment and money transfer

    # Get tracker list (unresolved only)
    response = auth_client.get(
        "/api/v1/status-tracker",
        params={"account_id": account.id, "status_group": "unresolved"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should have 2 unresolved items (payment and money transfer)
    assert data["unresolved_count"] == 2
    assert all(not item["is_final"] for item in data["items"])


def test_get_tracker_detail_with_timeline(auth_client, db_session):
    """Test getting tracker detail with timeline milestones."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.payment import Payment
    from app.models.tracking_event import TrackingEvent

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-TRACK-2",
        masked_name="Test C***",
        email="track2@example.com",
        phone_last_four="2222"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****2222",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
    )
    db_session.add(account)
    db_session.flush()

    # Create payment
    payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-DETAIL-1",
        payment_method="BankTransfer",
        amount=Decimal("150.00"),
        currency="GBP",
        status="Completed",
        processed_at=datetime.now(),
    )
    db_session.add(payment)
    db_session.flush()

    # Create tracking events
    events_data = [
        {"event_type": "submitted", "status": "Submitted", "occurred_at": datetime.now() - timedelta(hours=24)},
        {"event_type": "processing", "status": "Processing", "occurred_at": datetime.now() - timedelta(hours=12)},
        {"event_type": "completed", "status": "Completed", "occurred_at": datetime.now()},
    ]

    for evt_data in events_data:
        tracking_event = TrackingEvent(
            entity_type="Payment",
            entity_id=str(payment.id),
            event_type=evt_data["event_type"],
            status=evt_data["status"],
            event_data=f"Payment {evt_data['status'].lower()}",
            occurred_at=evt_data["occurred_at"],
        )
        db_session.add(tracking_event)

    db_session.commit()

    # Get tracker detail
    response = auth_client.get(
        f"/api/v1/status-tracker/Payment/{payment.id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "tracker_item" in data
    assert "milestones" in data
    assert "timeline_freshness" in data

    assert data["tracker_item"]["entity_type"] == "Payment"
    assert data["tracker_item"]["entity_id"] == str(payment.id)
    assert data["tracker_item"]["is_final"] is True

    # Should have 3 milestones in chronological order
    assert len(data["milestones"]) == 3
    assert data["milestones"][0]["milestone_label"] == "Submitted"
    assert data["milestones"][1]["milestone_label"] == "Processing"
    assert data["milestones"][2]["milestone_label"] == "Completed"


def test_get_tracker_detail_with_escalation(auth_client, db_session):
    """Test tracker detail with escalation for stalled item."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.payment import Payment

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-TRACK-3",
        masked_name="Test C***",
        email="track3@example.com",
        phone_last_four="3333"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****3333",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
    )
    db_session.add(account)
    db_session.flush()

    # Create payment that's been processing for over 30 minutes
    payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-STALLED-1",
        payment_method="BankTransfer",
        amount=Decimal("200.00"),
        currency="GBP",
        status="Processing",
        created_at=datetime.now() - timedelta(minutes=45),
        updated_at=datetime.now() - timedelta(minutes=45),
    )
    db_session.add(payment)
    db_session.commit()

    # Get tracker detail
    response = auth_client.get(
        f"/api/v1/status-tracker/Payment/{payment.id}"
    )

    assert response.status_code == 200
    data = response.json()

    # Should have escalation due to age > 30 minutes
    assert data["tracker_item"]["escalation"] is not None
    assert data["tracker_item"]["escalation"]["is_escalated"] is True
    assert "unresolved" in data["tracker_item"]["escalation"]["reason"].lower()


def test_tracker_refresh_success(auth_client, db_session):
    """Test successful tracker refresh."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.payment import Payment

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-TRACK-4",
        masked_name="Test C***",
        email="track4@example.com",
        phone_last_four="4444"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****4444",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
    )
    db_session.add(account)
    db_session.flush()

    # Create payment
    payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-REFRESH-1",
        payment_method="BankTransfer",
        amount=Decimal("100.00"),
        currency="GBP",
        status="Processing",
    )
    db_session.add(payment)
    db_session.commit()

    # Refresh tracker
    response = auth_client.post(
        f"/api/v1/status-tracker/Payment/{payment.id}/refresh"
    )

    assert response.status_code == 200
    data = response.json()

    assert "tracker_item" in data
    assert "refresh_outcome" in data
    assert "refresh_message" in data
    assert data["refresh_outcome"] in ["updated", "unchanged", "failed"]


def test_tracker_refresh_throttle(auth_client, db_session):
    """Test tracker refresh throttling."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.payment import Payment

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-TRACK-5",
        masked_name="Test C***",
        email="track5@example.com",
        phone_last_four="5555"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****5555",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
    )
    db_session.add(account)
    db_session.flush()

    # Create payment
    payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-THROTTLE-1",
        payment_method="BankTransfer",
        amount=Decimal("100.00"),
        currency="GBP",
        status="Processing",
    )
    db_session.add(payment)
    db_session.commit()

    # First refresh should succeed (or may be throttled if another test just ran)
    response = auth_client.post(
        f"/api/v1/status-tracker/Payment/{payment.id}/refresh"
    )
    # Accept either 200 (success) or 429 (throttled from prior test)
    # If throttled on first attempt, wait and retry
    if response.status_code == 429:
        import time
        time.sleep(11)  # Wait for throttle window
        response = auth_client.post(
            f"/api/v1/status-tracker/Payment/{payment.id}/refresh"
        )
    assert response.status_code == 200

    # Immediate second refresh should be throttled
    response = auth_client.post(
        f"/api/v1/status-tracker/Payment/{payment.id}/refresh"
    )
    assert response.status_code == 429
    assert "throttled" in response.json()["detail"].lower()


def test_get_tracker_list_pagination(auth_client, db_session):
    """Test tracker list pagination."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.payment import Payment

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-TRACK-6",
        masked_name="Test C***",
        email="track6@example.com",
        phone_last_four="6666"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****6666",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
    )
    db_session.add(account)
    db_session.flush()

    # Create 5 payments
    for i in range(5):
        payment = Payment(
            account_id=account.id,
            external_payment_id=f"PMT-PAGE-{i+1}",
            payment_method="BankTransfer",
            amount=Decimal("100.00"),
            currency="GBP",
            status="Processing",
        )
        db_session.add(payment)

    db_session.commit()

    # Request first page with limit=3
    response = auth_client.get(
        "/api/v1/status-tracker",
        params={"account_id": account.id, "limit": 3, "offset": 0}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 5
    assert len(data["items"]) == 3
    assert data["has_more"] is True


def test_tracker_detail_not_found(auth_client):
    """Test tracker detail for non-existent entity."""
    response = auth_client.get(
        "/api/v1/status-tracker/Payment/99999"
    )

    assert response.status_code == 404


def test_tracker_list_requires_auth(client, db_session):
    """Test that tracker list requires authentication."""
    response = client.get(
        "/api/v1/status-tracker",
        params={"account_id": 1}
    )

    assert response.status_code == 401

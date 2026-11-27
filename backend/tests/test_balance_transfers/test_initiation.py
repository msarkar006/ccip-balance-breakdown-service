"""
Tests for balance transfer initiation.
"""
from datetime import datetime, timedelta
from decimal import Decimal


def test_balance_transfer_initiation_happy_path(auth_client, db_session):
    """Test successful balance transfer initiation."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.offer import Offer
    from app.models.user_session import UserSession

    # Create customer
    customer = Customer(
        external_customer_id="CUST-BT-001",
        masked_name="Test C***",
        email="test@example.com",
        phone_last_four="1234"
    )
    db_session.add(customer)
    db_session.flush()

    # Create account
    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****1001",
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

    # Create balance transfer offer
    offer = Offer(
        account_id=account.id,
        offer_code="BT-TEST-2024",
        offer_title="Test Balance Transfer",
        offer_description="Test offer",
        offer_type="BalanceTransfer",
        status="Available",
        valid_from=datetime.now() - timedelta(days=1),
        valid_until=datetime.now() + timedelta(days=30)
    )
    db_session.add(offer)
    db_session.commit()

    # Update session with step-up
    session = db_session.query(UserSession).filter(
        UserSession.user_id == 1,
        UserSession.revoked_at.is_(None)
    ).first()
    if session:
        session.step_up_verified_at = datetime.now()
        db_session.commit()

    # Initiate transfer
    response = auth_client.post(
        "/api/v1/balance-transfers",
        json={
            "account_id": account.id,
            "offer_code": offer.offer_code,
            "transfer_amount": 500.00,
            "external_card_last4": "1234",
            "provider_name": "Test Bank",
            "idempotency_key": "test-bt-key-001"
        },
        headers={"Idempotency-Key": "test-bt-key-001"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] in ["Submitted", "ReviewRequired"]
    assert float(data["transfer_amount"]) == 500.00
    assert "external_transfer_id" in data


def test_balance_transfer_initiation_missing_step_up(auth_client, db_session):
    """Test that balance transfer initiation requires step-up."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.user_session import UserSession

    # Create customer
    customer = Customer(
        external_customer_id="CUST-BT-002",
        masked_name="Test C***",
        email="test2@example.com",
        phone_last_four="1234"
    )
    db_session.add(customer)
    db_session.flush()

    # Create account
    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****1001",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=15)
    )
    db_session.add(account)
    db_session.commit()

    # Clear step-up
    session = db_session.query(UserSession).filter(
        UserSession.user_id == 1,
        UserSession.revoked_at.is_(None)
    ).first()
    if session:
        session.step_up_verified_at = None
        db_session.commit()

    response = auth_client.post(
        "/api/v1/balance-transfers",
        json={
            "account_id": account.id,
            "offer_code": "BT-PROMO-2024",
            "transfer_amount": 500.00,
            "external_card_last4": "1234",
            "provider_name": "Test Bank",
            "idempotency_key": "test-bt-key-002"
        },
        headers={"Idempotency-Key": "test-bt-key-002"}
    )

    assert response.status_code == 403


def test_balance_transfer_initiation_idempotency(auth_client, db_session):
    """Test idempotent replay of balance transfer initiation."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.offer import Offer
    from app.models.user_session import UserSession

    # Create customer
    customer = Customer(
        external_customer_id="CUST-BT-003",
        masked_name="Test C***",
        email="test3@example.com",
        phone_last_four="1234"
    )
    db_session.add(customer)
    db_session.flush()

    # Create account
    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****1001",
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

    # Create balance transfer offer
    offer = Offer(
        account_id=account.id,
        offer_code="BT-TEST-2024",
        offer_title="Test Balance Transfer",
        offer_description="Test offer",
        offer_type="BalanceTransfer",
        status="Available",
        valid_from=datetime.now() - timedelta(days=1),
        valid_until=datetime.now() + timedelta(days=30)
    )
    db_session.add(offer)
    db_session.commit()

    # Update session with step-up
    session = db_session.query(UserSession).filter(
        UserSession.user_id == 1,
        UserSession.revoked_at.is_(None)
    ).first()
    if session:
        session.step_up_verified_at = datetime.now()
        db_session.commit()

    payload = {
        "account_id": account.id,
        "offer_code": offer.offer_code,
        "transfer_amount": 500.00,
        "external_card_last4": "1234",
        "provider_name": "Test Bank",
        "idempotency_key": "test-bt-key-003"
    }

    # First request
    response1 = auth_client.post(
        "/api/v1/balance-transfers",
        json=payload,
        headers={"Idempotency-Key": "test-bt-key-003"}
    )
    assert response1.status_code == 201

    # Replay with same key and payload
    response2 = auth_client.post(
        "/api/v1/balance-transfers",
        json=payload,
        headers={"Idempotency-Key": "test-bt-key-003"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["idempotent_replay"] is True

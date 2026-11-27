"""
Tests for money transfer initiation.
"""
from datetime import datetime, timedelta
from decimal import Decimal


def test_money_transfer_initiation_happy_path(auth_client, db_session):
    """Test successful money transfer initiation."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.payee import Payee
    from app.models.user_session import UserSession

    # Create customer
    customer = Customer(
        external_customer_id="CUST-MT-001",
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

    # Create payee
    payee = Payee(
        account_id=account.id,
        payee_name="Test Payee",
        account_number_masked="****5678",
        sort_code_masked="11-22-33",
        is_active=True
    )
    db_session.add(payee)
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
        "/api/v1/money-transfers",
        json={
            "account_id": account.id,
            "payee_id": payee.id,
            "amount": 100.00,
            "currency": "GBP",
            "idempotency_key": "test-mt-key-001"
        },
        headers={"Idempotency-Key": "test-mt-key-001"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] in ["Submitted", "Processing"]
    assert float(data["amount"]) == 100.00
    assert "external_transfer_id" in data


def test_money_transfer_initiation_missing_step_up(auth_client, db_session):
    """Test that money transfer initiation requires step-up."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.payee import Payee
    from app.models.user_session import UserSession

    # Create customer
    customer = Customer(
        external_customer_id="CUST-MT-002",
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
    db_session.flush()

    # Create payee
    payee = Payee(
        account_id=account.id,
        payee_name="Test Payee",
        account_number_masked="****5678",
        sort_code_masked="11-22-33",
        is_active=True
    )
    db_session.add(payee)
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
        "/api/v1/money-transfers",
        json={
            "account_id": account.id,
            "payee_id": payee.id,
            "amount": 100.00,
            "currency": "GBP",
            "idempotency_key": "test-mt-key-002"
        },
        headers={"Idempotency-Key": "test-mt-key-002"}
    )

    assert response.status_code == 403


def test_money_transfer_initiation_idempotency(auth_client, db_session):
    """Test idempotent replay of money transfer initiation."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.payee import Payee
    from app.models.user_session import UserSession

    # Create customer
    customer = Customer(
        external_customer_id="CUST-MT-003",
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

    # Create payee
    payee = Payee(
        account_id=account.id,
        payee_name="Test Payee",
        account_number_masked="****5678",
        sort_code_masked="11-22-33",
        is_active=True
    )
    db_session.add(payee)
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
        "payee_id": payee.id,
        "amount": 100.00,
        "currency": "GBP",
        "idempotency_key": "test-mt-key-003"
    }

    # First request
    response1 = auth_client.post(
        "/api/v1/money-transfers",
        json=payload,
        headers={"Idempotency-Key": "test-mt-key-003"}
    )
    assert response1.status_code == 201

    # Replay with same key and payload
    response2 = auth_client.post(
        "/api/v1/money-transfers",
        json=payload,
        headers={"Idempotency-Key": "test-mt-key-003"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["idempotent_replay"] is True

"""
Tests for payment initiation endpoint.
"""
from datetime import datetime, timedelta
from decimal import Decimal


def test_payment_initiation_happy_path(auth_client, db_session):
    """Test successful payment initiation returns 201 with Submitted status."""
    from app.models.credit_card_account import CreditCardAccount

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****9001",
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

    # Perform step-up first
    auth_client.post("/api/v1/auth/step-up", json={"password": "admin123"})

    # Initiate payment
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "account_id": account.id,
            "amount": "100.00",
            "currency": "GBP",
            "payment_method": "BankTransfer",
            "scheduled_date": None,
            "idempotency_key": "test-key-001"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["account_id"] == account.id
    assert Decimal(data["amount"]) == Decimal("100.00")
    assert data["currency"] == "GBP"
    assert data["status"] == "Submitted"
    assert data["idempotency_key"] == "test-key-001"
    assert "external_payment_id" in data
    assert data["guidance"] is None


def test_payment_initiation_idempotency_replay(auth_client, db_session):
    """Test idempotent replay returns existing payment."""
    from app.models.credit_card_account import CreditCardAccount

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****9002",
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

    # Perform step-up
    auth_client.post("/api/v1/auth/step-up", json={"password": "admin123"})

    # First payment
    response1 = auth_client.post(
        "/api/v1/payments",
        json={
            "account_id": account.id,
            "amount": "150.00",
            "currency": "GBP",
            "payment_method": "BankTransfer",
            "scheduled_date": None,
            "idempotency_key": "idempotent-key-001"
        }
    )
    assert response1.status_code == 201
    payment_id = response1.json()["id"]

    # Replay with same idempotency key
    response2 = auth_client.post(
        "/api/v1/payments",
        json={
            "account_id": account.id,
            "amount": "150.00",
            "currency": "GBP",
            "payment_method": "BankTransfer",
            "scheduled_date": None,
            "idempotency_key": "idempotent-key-001"
        }
    )
    assert response2.status_code == 201
    assert response2.json()["id"] == payment_id


def test_payment_initiation_step_up_missing(auth_client, db_session):
    """Test payment initiation without step-up returns 403."""
    from app.models.credit_card_account import CreditCardAccount

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****9003",
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

    # Attempt payment without step-up
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "account_id": account.id,
            "amount": "100.00",
            "currency": "GBP",
            "payment_method": "BankTransfer",
            "scheduled_date": None,
            "idempotency_key": "test-key-002"
        }
    )

    assert response.status_code == 403
    assert "step-up" in response.json()["detail"].lower()


def test_payment_initiation_invalid_amount_zero(auth_client, db_session):
    """Test payment with amount = 0 returns 422."""
    from app.models.credit_card_account import CreditCardAccount

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****9004",
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

    # Perform step-up
    auth_client.post("/api/v1/auth/step-up", json={"password": "admin123"})

    # Attempt payment with zero amount
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "account_id": account.id,
            "amount": "0.00",
            "currency": "GBP",
            "payment_method": "BankTransfer",
            "scheduled_date": None,
            "idempotency_key": "test-key-003"
        }
    )

    assert response.status_code == 422


def test_payment_initiation_exceeds_balance(auth_client, db_session):
    """Test payment exceeding balance returns 422."""
    from app.models.credit_card_account import CreditCardAccount

    # Create test account with low balance
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****9005",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("4500.00"),
        current_balance=Decimal("500.00"),
        minimum_payment_due=Decimal("25.00"),
        payment_due_date=datetime.now() + timedelta(days=15)
    )
    db_session.add(account)
    db_session.commit()

    # Perform step-up
    auth_client.post("/api/v1/auth/step-up", json={"password": "admin123"})

    # Attempt payment exceeding balance
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "account_id": account.id,
            "amount": "1000.00",
            "currency": "GBP",
            "payment_method": "BankTransfer",
            "scheduled_date": None,
            "idempotency_key": "test-key-004"
        }
    )

    assert response.status_code == 422
    assert "balance" in response.json()["detail"].lower()


def test_payment_guidance(auth_client, db_session):
    """Test payment guidance endpoint returns guidance with DirectDebit coverage."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.direct_debit_mandate import DirectDebitMandate

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****9006",
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

    # Create active mandate
    mandate = DirectDebitMandate(
        account_id=account.id,
        mandate_reference="DD-TEST-001",
        mandate_type="MinimumPayment",
        payment_amount=None,
        status="Active",
        activated_at=datetime.now() - timedelta(days=10)
    )
    db_session.add(mandate)
    db_session.commit()

    # Get payment guidance
    response = auth_client.get(f"/api/v1/payments/guidance?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["minimum_payment"]) == Decimal("100.00")
    assert Decimal(data["current_balance"]) == Decimal("2000.00")
    assert Decimal(data["max_payment_amount"]) == Decimal("2000.00")
    assert "direct_debit_coverage" in data
    assert data["direct_debit_coverage"]["coverage_status"] in [
        "expected_to_cover",
        "not_expected_to_cover",
        "cannot_be_confirmed"
    ]
    assert isinstance(data["direct_debit_coverage"]["manual_payment_may_be_required"], bool)

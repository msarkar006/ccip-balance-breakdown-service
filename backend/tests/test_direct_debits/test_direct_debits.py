"""
Tests for direct debit endpoints.
"""
from datetime import datetime, timedelta
from decimal import Decimal


def test_get_direct_debits(auth_client, db_session):
    """Test GET /direct-debits returns mandates for account."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.direct_debit_mandate import DirectDebitMandate

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****8001",
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

    # Create mandates
    mandate1 = DirectDebitMandate(
        account_id=account.id,
        mandate_reference="DD-TEST-001",
        mandate_type="MinimumPayment",
        payment_amount=None,
        status="Active",
        activated_at=datetime.now() - timedelta(days=60)
    )
    mandate2 = DirectDebitMandate(
        account_id=account.id,
        mandate_reference="DD-TEST-002",
        mandate_type="FixedAmount",
        payment_amount=Decimal("50.00"),
        status="Cancelled",
        activated_at=datetime.now() - timedelta(days=90)
    )
    db_session.add(mandate1)
    db_session.add(mandate2)
    db_session.commit()

    # Get mandates
    response = auth_client.get(f"/api/v1/direct-debits?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()
    assert "mandates" in data
    assert len(data["mandates"]) == 2
    # Verify they're ordered by created_at DESC
    assert data["mandates"][0]["mandate_reference"] == "DD-TEST-002"
    assert data["mandates"][1]["mandate_reference"] == "DD-TEST-001"


def test_direct_debit_coverage_expected_to_cover(auth_client, db_session):
    """Test coverage derivation returns expected_to_cover for active MinimumPayment with recent collection."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.direct_debit_mandate import DirectDebitMandate
    from app.models.payment import Payment

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****8002",
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

    # Create active MinimumPayment mandate
    mandate = DirectDebitMandate(
        account_id=account.id,
        mandate_reference="DD-TEST-003",
        mandate_type="MinimumPayment",
        payment_amount=None,
        status="Active",
        activated_at=datetime.now() - timedelta(days=60)
    )
    db_session.add(mandate)

    # Create recent DirectDebit payment (within 35 days)
    payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-DD-001",
        idempotency_key=None,
        payment_method="DirectDebit",
        amount=Decimal("100.00"),
        currency="GBP",
        status="Completed",
        scheduled_date=None,
        processed_at=datetime.now() - timedelta(days=10),
        created_at=datetime.now() - timedelta(days=10),
        updated_at=datetime.now() - timedelta(days=10)
    )
    db_session.add(payment)
    db_session.commit()

    # Get payment guidance (which includes coverage)
    response = auth_client.get(f"/api/v1/payments/guidance?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()
    coverage = data["direct_debit_coverage"]
    assert coverage["coverage_status"] == "expected_to_cover"
    assert coverage["manual_payment_may_be_required"] is False


def test_direct_debit_coverage_cannot_be_confirmed(auth_client, db_session):
    """Test coverage derivation returns cannot_be_confirmed when no active mandate."""
    from app.models.credit_card_account import CreditCardAccount

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****8003",
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

    # No mandate created

    # Get payment guidance
    response = auth_client.get(f"/api/v1/payments/guidance?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()
    coverage = data["direct_debit_coverage"]
    assert coverage["coverage_status"] == "cannot_be_confirmed"
    assert coverage["manual_payment_may_be_required"] is True
    assert "no active" in coverage["reason"].lower()


def test_direct_debit_coverage_not_expected_to_cover(auth_client, db_session):
    """Test coverage derivation returns not_expected_to_cover for FixedAmount below minimum."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.direct_debit_mandate import DirectDebitMandate

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****8004",
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

    # Create FixedAmount mandate with payment_amount < minimum_payment
    mandate = DirectDebitMandate(
        account_id=account.id,
        mandate_reference="DD-TEST-004",
        mandate_type="FixedAmount",
        payment_amount=Decimal("50.00"),
        status="Active",
        activated_at=datetime.now() - timedelta(days=60)
    )
    db_session.add(mandate)
    db_session.commit()

    # Get payment guidance
    response = auth_client.get(f"/api/v1/payments/guidance?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()
    coverage = data["direct_debit_coverage"]
    assert coverage["coverage_status"] == "not_expected_to_cover"
    assert coverage["manual_payment_may_be_required"] is True


def test_change_request_happy_path(auth_client, db_session):
    """Test successful change request initiation returns 201."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.direct_debit_mandate import DirectDebitMandate

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****8005",
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

    # Create mandate
    mandate = DirectDebitMandate(
        account_id=account.id,
        mandate_reference="DD-TEST-005",
        mandate_type="FixedAmount",
        payment_amount=Decimal("50.00"),
        status="Active",
        activated_at=datetime.now() - timedelta(days=60)
    )
    db_session.add(mandate)
    db_session.commit()

    # Perform step-up
    auth_client.post("/api/v1/auth/step-up", json={"password": "admin123"})

    # Create change request
    response = auth_client.post(
        "/api/v1/direct-debits/change-requests",
        json={
            "mandate_id": mandate.id,
            "change_type": "Amend",
            "new_payment_amount": "120.00",
            "idempotency_key": "change-key-001"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["mandate_id"] == mandate.id
    assert data["change_type"] == "Amend"
    assert Decimal(data["new_payment_amount"]) == Decimal("120.00")
    assert data["status"] == "Submitted"


def test_change_request_idempotency(auth_client, db_session):
    """Test idempotent replay of change request."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.direct_debit_mandate import DirectDebitMandate

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****8006",
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

    # Create mandate
    mandate = DirectDebitMandate(
        account_id=account.id,
        mandate_reference="DD-TEST-006",
        mandate_type="MinimumPayment",
        payment_amount=None,
        status="Active",
        activated_at=datetime.now() - timedelta(days=60)
    )
    db_session.add(mandate)
    db_session.commit()

    # Perform step-up
    auth_client.post("/api/v1/auth/step-up", json={"password": "admin123"})

    # First change request
    response1 = auth_client.post(
        "/api/v1/direct-debits/change-requests",
        json={
            "mandate_id": mandate.id,
            "change_type": "Cancel",
            "new_payment_amount": None,
            "idempotency_key": "change-key-idempotent"
        }
    )
    assert response1.status_code == 201
    change_id = response1.json()["id"]

    # Replay with same idempotency key
    response2 = auth_client.post(
        "/api/v1/direct-debits/change-requests",
        json={
            "mandate_id": mandate.id,
            "change_type": "Cancel",
            "new_payment_amount": None,
            "idempotency_key": "change-key-idempotent"
        }
    )
    assert response2.status_code == 201
    assert response2.json()["id"] == change_id


def test_change_request_step_up_required(auth_client, db_session):
    """Test change request without step-up returns 403."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.direct_debit_mandate import DirectDebitMandate

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****8007",
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

    # Create mandate
    mandate = DirectDebitMandate(
        account_id=account.id,
        mandate_reference="DD-TEST-007",
        mandate_type="FixedAmount",
        payment_amount=Decimal("50.00"),
        status="Active",
        activated_at=datetime.now() - timedelta(days=60)
    )
    db_session.add(mandate)
    db_session.commit()

    # Attempt change request without step-up
    response = auth_client.post(
        "/api/v1/direct-debits/change-requests",
        json={
            "mandate_id": mandate.id,
            "change_type": "Cancel",
            "new_payment_amount": None,
            "idempotency_key": "change-key-002"
        }
    )

    assert response.status_code == 403
    assert "step-up" in response.json()["detail"].lower()

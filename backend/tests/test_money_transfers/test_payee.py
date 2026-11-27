"""
Tests for payee list retrieval.
"""
from datetime import datetime, timedelta
from decimal import Decimal


def test_get_payees_success(auth_client, db_session):
    """Test successful retrieval of payee list."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.payee import Payee

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-001",
        masked_name="Test C***",
        email="test@example.com",
        phone_last_four="1234"
    )
    db_session.add(customer)
    db_session.flush()

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

    # Create a payee
    payee = Payee(
        account_id=account.id,
        payee_name="Test Payee",
        account_number_masked="****5678",
        sort_code_masked="12-34-56",
        is_active=True
    )
    db_session.add(payee)
    db_session.commit()

    response = auth_client.get(f"/api/v1/payees?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) > 0

    # Verify masking
    for payee in data["items"]:
        assert "*" in payee["account_number_masked"]
        assert "*" in payee["sort_code_masked"] or "-" in payee["sort_code_masked"]


def test_get_payees_pagination(auth_client, db_session):
    """Test payee list pagination."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.payee import Payee

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-002",
        masked_name="Test C***",
        email="test2@example.com",
        phone_last_four="5678"
    )
    db_session.add(customer)
    db_session.flush()

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

    # Create multiple payees
    for i in range(3):
        payee = Payee(
            account_id=account.id,
            payee_name=f"Test Payee {i+1}",
            account_number_masked=f"****{1000+i}",
            sort_code_masked="12-34-56",
            is_active=True
        )
        db_session.add(payee)
    db_session.commit()

    response = auth_client.get(f"/api/v1/payees?account_id={account.id}&limit=1&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert "has_more" in data

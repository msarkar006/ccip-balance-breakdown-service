"""
Tests for account list endpoint.
"""
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.credit_card_account import CreditCardAccount
from app.models.customer import Customer


def test_list_accounts_success(auth_client: TestClient, db_session: Session):
    """Test successful account list retrieval."""
    # Use customer_id=1 created by auth_client fixture
    customer_id = 1

    # Create accounts
    account1 = CreditCardAccount(
        customer_id=customer_id,
        account_number_masked="****1001",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=15)
    )
    account2 = CreditCardAccount(
        customer_id=customer_id,
        account_number_masked="****1002",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("10000.00"),
        available_credit=Decimal("8000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=20)
    )
    db_session.add(account1)
    db_session.add(account2)
    db_session.commit()

    # List accounts
    response = auth_client.get("/api/v1/accounts")

    assert response.status_code == 200
    data = response.json()

    assert "accounts" in data
    assert len(data["accounts"]) == 2

    account = data["accounts"][0]
    assert "id" in account
    assert "account_number_masked" in account
    assert "account_status" in account
    assert "current_balance" in account
    assert "available_credit" in account
    assert "credit_limit" in account


def test_list_accounts_empty(auth_client: TestClient, db_session: Session):
    """Test account list when no accounts exist."""
    # auth_client fixture creates customer_id=1 but no accounts
    # so this should return an empty list
    response = auth_client.get("/api/v1/accounts")

    assert response.status_code == 200
    data = response.json()

    assert "accounts" in data
    assert len(data["accounts"]) == 0


def test_list_accounts_without_auth(client: TestClient):
    """Test account list without authentication."""
    response = client.get("/api/v1/accounts")

    assert response.status_code == 401

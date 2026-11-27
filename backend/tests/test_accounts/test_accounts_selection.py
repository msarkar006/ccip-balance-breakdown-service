"""
Tests for account selection endpoint.
"""
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.credit_card_account import CreditCardAccount
from app.models.customer import Customer


def test_select_account_success(auth_client: TestClient, db_session: Session):
    """Test successful account selection."""
    # Use customer_id=1 created by auth_client fixture
    customer_id = 1

    # Create account
    account = CreditCardAccount(
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
    db_session.add(account)
    db_session.commit()

    # Select account
    response = auth_client.put(
        "/api/v1/accounts/selection",
        json={"account_id": account.id}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["selected_account_id"] == account.id
    assert "message" in data

    # Verify selection persisted
    me_response = auth_client.get("/api/v1/auth/me")
    assert me_response.json()["selected_account_id"] == account.id


def test_clear_account_selection(auth_client: TestClient, db_session: Session):
    """Test clearing account selection."""
    # Use customer_id=1 created by auth_client fixture
    customer_id = 1

    account = CreditCardAccount(
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
    db_session.add(account)
    db_session.commit()

    # Select account first
    select_response = auth_client.put(
        "/api/v1/accounts/selection",
        json={"account_id": account.id}
    )
    assert select_response.status_code == 200

    # Clear selection
    clear_response = auth_client.put(
        "/api/v1/accounts/selection",
        json={"account_id": None}
    )

    assert clear_response.status_code == 200
    data = clear_response.json()

    assert data["success"] is True
    assert data["selected_account_id"] is None

    # Verify selection cleared
    me_response = auth_client.get("/api/v1/auth/me")
    assert me_response.json()["selected_account_id"] is None


def test_select_nonexistent_account(auth_client: TestClient):
    """Test selecting a non-existent account."""
    response = auth_client.put(
        "/api/v1/accounts/selection",
        json={"account_id": 99999}
    )

    # Security: Returns 403 (forbidden) instead of 404 to avoid leaking which accounts exist
    assert response.status_code == 403


def test_select_account_without_auth(client: TestClient):
    """Test account selection without authentication."""
    response = client.put(
        "/api/v1/accounts/selection",
        json={"account_id": 1}
    )

    assert response.status_code == 401

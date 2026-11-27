"""
Tests for account overview endpoint.
"""
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.credit_card import CreditCard
from app.models.credit_card_account import CreditCardAccount
from app.models.customer import Customer


def test_get_account_overview_success(auth_client: TestClient, db_session: Session):
    """Test successful account overview retrieval."""
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
    db_session.flush()

    # Create card
    card = CreditCard(
        account_id=account.id,
        card_number_masked="****-****-****-1234",
        card_type="Visa",
        card_status="Active",
        expiry_month=12,
        expiry_year=2026
    )
    db_session.add(card)
    db_session.commit()

    # Get overview
    response = auth_client.get(f"/api/v1/accounts/{account.id}/overview")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == account.id
    assert data["account_number_masked"] == "****1001"
    assert data["sort_code_masked"] == "12-34-56"
    assert data["account_status"] == "Active"
    assert data["credit_limit"] == "5000.00"
    assert data["available_credit"] == "3000.00"
    assert data["current_balance"] == "2000.00"
    assert data["minimum_payment_due"] == "100.00"
    assert "payment_due_date" in data

    assert "cards" in data
    assert len(data["cards"]) == 1
    card_data = data["cards"][0]
    assert card_data["card_number_masked"] == "****-****-****-1234"
    assert card_data["card_type"] == "Visa"
    assert card_data["card_status"] == "Active"

    assert data["freshness"] == "Current"
    assert "as_of" in data


def test_get_account_overview_not_found(auth_client: TestClient, db_session: Session):
    """Test account overview for non-existent account."""
    response = auth_client.get("/api/v1/accounts/99999/overview")

    # Security: Returns 403 (forbidden) instead of 404 to avoid leaking which accounts exist
    assert response.status_code == 403


def test_get_account_overview_without_auth(client: TestClient):
    """Test account overview without authentication."""
    response = client.get("/api/v1/accounts/1/overview")

    assert response.status_code == 401


def test_get_account_overview_no_cards(auth_client: TestClient, db_session: Session):
    """Test account overview for account with no cards."""
    # Use customer_id=1 created by auth_client fixture
    customer_id = 1

    # Create account without cards
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

    # Get overview
    response = auth_client.get(f"/api/v1/accounts/{account.id}/overview")

    assert response.status_code == 200
    data = response.json()

    assert "cards" in data
    assert len(data["cards"]) == 0

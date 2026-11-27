"""
Tests for offers endpoints.
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models.credit_card_account import CreditCardAccount
from app.models.customer import Customer
from app.models.offer import Offer


@pytest.fixture
def test_customer(db_session):
    """Create a test customer."""
    customer = Customer(
        external_customer_id="TEST-CUST-002",
        masked_name="Test O***",
        email="offers@example.com",
        phone_last_four="5678"
    )
    db_session.add(customer)
    db_session.commit()
    return customer


@pytest.fixture
def test_account(db_session, test_customer):
    """Create a test account."""
    account = CreditCardAccount(
        customer_id=test_customer.id,
        account_number_masked="****8888",
        sort_code_masked="44-55-66",
        account_status="Active",
        credit_limit=Decimal("10000.00"),
        available_credit=Decimal("8000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=20),
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def test_offers(db_session, test_account):
    """Create test offers."""
    offers = [
        Offer(
            account_id=test_account.id,
            offer_code="TEST-BT-001",
            offer_title="0% Balance Transfer",
            offer_description="Transfer your balance with 0% interest",
            offer_type="BalanceTransfer",
            status="Available",
            valid_from=datetime.now() - timedelta(days=5),
            valid_until=datetime.now() + timedelta(days=85),
        ),
        Offer(
            account_id=test_account.id,
            offer_code="TEST-BT-002",
            offer_title="Low Rate Balance Transfer",
            offer_description="3.9% balance transfer",
            offer_type="BalanceTransfer",
            status="Active",
            valid_from=datetime.now() - timedelta(days=10),
            valid_until=datetime.now() + timedelta(days=80),
        ),
        Offer(
            account_id=test_account.id,
            offer_code="TEST-RWD-001",
            offer_title="Double Rewards",
            offer_description="Earn 2x rewards points",
            offer_type="Rewards",
            status="Available",
            valid_from=datetime.now() - timedelta(days=3),
            valid_until=datetime.now() + timedelta(days=87),
        ),
        Offer(
            account_id=test_account.id,
            offer_code="TEST-INS-001",
            offer_title="Flexible Instalments",
            offer_description="Convert purchases to instalments",
            offer_type="Instalment",
            status="Available",
            valid_from=datetime.now() - timedelta(days=7),
            valid_until=datetime.now() + timedelta(days=83),
        ),
        Offer(
            account_id=test_account.id,
            offer_code="TEST-EXP-001",
            offer_title="Expired Offer",
            offer_description="This offer has expired",
            offer_type="BalanceTransfer",
            status="Expired",
            valid_from=datetime.now() - timedelta(days=100),
            valid_until=datetime.now() - timedelta(days=10),
        ),
    ]

    for offer in offers:
        db_session.add(offer)

    db_session.commit()
    return offers


def test_list_offers_all(auth_client, test_account, test_offers):
    """Test listing all offers for an account."""
    response = auth_client.get(f"/api/v1/offers?account_id={test_account.id}")

    assert response.status_code == 200
    data = response.json()

    # Should return only Available or Active offers (4 out of 5)
    assert len(data["items"]) == 4
    assert data["total"] == 4
    assert data["limit"] == 20
    assert data["offset"] == 0
    assert data["has_more"] is False

    # Verify no expired offers
    offer_codes = [item["offer_code"] for item in data["items"]]
    assert "TEST-EXP-001" not in offer_codes


def test_list_offers_by_context_balance_transfer(auth_client, test_account, test_offers):
    """Test filtering offers by context (BalanceTransfer)."""
    response = auth_client.get(
        f"/api/v1/offers?account_id={test_account.id}&context=BalanceTransfer"
    )

    assert response.status_code == 200
    data = response.json()

    # Should return 2 BalanceTransfer offers (excluding expired)
    assert len(data["items"]) == 2
    assert data["total"] == 2

    for item in data["items"]:
        assert item["offer_type"] == "BalanceTransfer"
        assert item["status"] in ["Available", "Active"]


def test_list_offers_by_context_rewards(auth_client, test_account, test_offers):
    """Test filtering offers by context (Rewards)."""
    response = auth_client.get(
        f"/api/v1/offers?account_id={test_account.id}&context=Rewards"
    )

    assert response.status_code == 200
    data = response.json()

    # Should return 1 Rewards offer
    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert data["items"][0]["offer_type"] == "Rewards"


def test_list_offers_by_context_instalment(auth_client, test_account, test_offers):
    """Test filtering offers by context (Instalment)."""
    response = auth_client.get(
        f"/api/v1/offers?account_id={test_account.id}&context=Instalment"
    )

    assert response.status_code == 200
    data = response.json()

    # Should return 1 Instalment offer
    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert data["items"][0]["offer_type"] == "Instalment"


def test_list_offers_pagination(auth_client, db_session, test_account):
    """Test offer pagination."""
    # Create 25 offers
    for i in range(25):
        offer = Offer(
            account_id=test_account.id,
            offer_code=f"TEST-PAG-{i:03d}",
            offer_title=f"Test Offer {i}",
            offer_description=f"Description {i}",
            offer_type="BalanceTransfer",
            status="Available",
            valid_from=datetime.now() - timedelta(days=1),
            valid_until=datetime.now() + timedelta(days=89),
        )
        db_session.add(offer)

    db_session.commit()

    # First page
    response = auth_client.get(
        f"/api/v1/offers?account_id={test_account.id}&limit=10&offset=0"
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 10
    assert data["total"] == 25
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["has_more"] is True

    # Second page
    response = auth_client.get(
        f"/api/v1/offers?account_id={test_account.id}&limit=10&offset=10"
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 10
    assert data["total"] == 25
    assert data["limit"] == 10
    assert data["offset"] == 10
    assert data["has_more"] is True

    # Third page
    response = auth_client.get(
        f"/api/v1/offers?account_id={test_account.id}&limit=10&offset=20"
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 5
    assert data["total"] == 25
    assert data["limit"] == 10
    assert data["offset"] == 20
    assert data["has_more"] is False


def test_list_offers_empty_results(auth_client, db_session, test_customer):
    """Test listing offers for account with no offers."""
    # Create account with no offers
    account = CreditCardAccount(
        customer_id=test_customer.id,
        account_number_masked="****7777",
        sort_code_masked="11-22-33",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("5000.00"),
        current_balance=Decimal("0.00"),
        minimum_payment_due=Decimal("0.00"),
        payment_due_date=datetime.now() + timedelta(days=30),
    )
    db_session.add(account)
    db_session.commit()

    response = auth_client.get(f"/api/v1/offers?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 0
    assert data["total"] == 0
    assert data["has_more"] is False


def test_list_offers_requires_auth(client, test_account):
    """Test that offers endpoint requires authentication."""
    response = client.get(f"/api/v1/offers?account_id={test_account.id}")

    assert response.status_code == 401


def test_list_offers_invalid_context(auth_client, test_account):
    """Test listing offers with invalid context filter."""
    # This should still work, just return no results since no offers match
    response = auth_client.get(
        f"/api/v1/offers?account_id={test_account.id}&context=InvalidContext"
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 0
    assert data["total"] == 0

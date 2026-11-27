"""
Tests for balance breakdown endpoints.
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models.balance_breakdown import BalanceBreakdown
from app.models.balance_category import BalanceCategory
from app.models.balance_transfer import BalanceTransfer
from app.models.credit_card_account import CreditCardAccount
from app.models.customer import Customer


@pytest.fixture
def test_customer(db_session):
    """Create a test customer."""
    customer = Customer(
        external_customer_id="TEST-CUST-001",
        masked_name="Test C***",
        email="test@example.com",
        phone_last_four="1234"
    )
    db_session.add(customer)
    db_session.commit()
    return customer


@pytest.fixture
def test_account(db_session, test_customer):
    """Create a test account."""
    account = CreditCardAccount(
        customer_id=test_customer.id,
        account_number_masked="****9999",
        sort_code_masked="11-22-33",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=15),
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def test_breakdown_with_categories(db_session, test_account):
    """Create a test balance breakdown with categories."""
    breakdown = BalanceBreakdown(
        account_id=test_account.id,
        total_balance=Decimal("2000.00"),
        snapshot_date=datetime.now(),
    )
    db_session.add(breakdown)
    db_session.flush()

    # Add categories
    categories = [
        BalanceCategory(
            breakdown_id=breakdown.id,
            category_name="StandardPurchase",
            category_amount=Decimal("1000.00"),
            apr=Decimal("19.90"),
            display_rank=1,
        ),
        BalanceCategory(
            breakdown_id=breakdown.id,
            category_name="PromotionalPurchase",
            category_amount=Decimal("500.00"),
            apr=Decimal("0.00"),
            display_rank=2,
            promo_rate=Decimal("0.00"),
            promo_end_date=datetime.now() + timedelta(days=90),
        ),
        BalanceCategory(
            breakdown_id=breakdown.id,
            category_name="BalanceTransfer",
            category_amount=Decimal("500.00"),
            apr=Decimal("0.00"),
            display_rank=3,
        ),
    ]

    for cat in categories:
        db_session.add(cat)

    db_session.commit()
    return breakdown


def test_get_current_breakdown_success(auth_client, test_breakdown_with_categories, test_account):
    """Test retrieving current balance breakdown."""
    response = auth_client.get(f"/api/v1/balance-breakdowns/current?account_id={test_account.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == test_breakdown_with_categories.id
    assert data["account_id"] == test_account.id
    assert Decimal(data["total_balance"]) == Decimal("2000.00")
    assert Decimal(data["pending_total"]) == Decimal("0.00")
    assert len(data["categories"]) == 3

    # Check categories are ordered by display_rank
    assert data["categories"][0]["category_name"] == "StandardPurchase"
    assert data["categories"][1]["category_name"] == "PromotionalPurchase"
    assert data["categories"][2]["category_name"] == "BalanceTransfer"

    # Check freshness object
    assert "freshness" in data
    assert data["freshness"]["level"] == "Current"
    assert "as_of" in data["freshness"]


def test_get_current_breakdown_not_found(auth_client):
    """Test retrieving breakdown for non-existent account."""
    response = auth_client.get("/api/v1/balance-breakdowns/current?account_id=99999")

    assert response.status_code == 404
    assert "detail" in response.json()


def test_get_current_breakdown_with_source_linkage(
    auth_client, db_session, test_account, test_breakdown_with_categories
):
    """Test retrieving breakdown with source linkage to balance transfer."""
    # Create a balance transfer
    transfer = BalanceTransfer(
        account_id=test_account.id,
        external_transfer_id="BT-TEST-001",
        transfer_amount=Decimal("500.00"),
        promotional_rate=Decimal("0.00"),
        promotional_period_months=12,
        status="Completed",
        processed_at=datetime.now() - timedelta(days=10),
    )
    db_session.add(transfer)
    db_session.flush()

    # Link the BalanceTransfer category to this transfer
    bt_category = db_session.query(BalanceCategory).filter(
        BalanceCategory.breakdown_id == test_breakdown_with_categories.id,
        BalanceCategory.category_name == "BalanceTransfer"
    ).first()
    bt_category.source_balance_transfer_id = transfer.id
    db_session.commit()

    # Retrieve breakdown
    response = auth_client.get(f"/api/v1/balance-breakdowns/current?account_id={test_account.id}")

    assert response.status_code == 200
    data = response.json()

    # Find the BalanceTransfer category
    bt_cat = next(c for c in data["categories"] if c["category_name"] == "BalanceTransfer")

    assert bt_cat["source_link"] is not None
    assert bt_cat["source_link"]["source_type"] == "BalanceTransfer"
    assert bt_cat["source_link"]["source_id"] == transfer.id
    assert bt_cat["source_link"]["source_reference"] == "BT-TEST-001"


def test_get_category_detail_success(auth_client, test_breakdown_with_categories):
    """Test retrieving category detail."""
    # Get first category
    category = test_breakdown_with_categories

    response = auth_client.get(
        f"/api/v1/balance-breakdowns/{test_breakdown_with_categories.id}/categories/1"
    )

    # Category ID is auto-increment, so we need to get the actual first category
    from app.core.database import SessionLocal
    from app.models.balance_category import BalanceCategory

    db = SessionLocal()
    first_cat = db.query(BalanceCategory).filter(
        BalanceCategory.breakdown_id == test_breakdown_with_categories.id
    ).order_by(BalanceCategory.id).first()
    db.close()

    response = auth_client.get(
        f"/api/v1/balance-breakdowns/{test_breakdown_with_categories.id}/categories/{first_cat.id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == first_cat.id
    assert data["breakdown_id"] == test_breakdown_with_categories.id
    assert data["category_name"] == "StandardPurchase"
    assert Decimal(data["category_amount"]) == Decimal("1000.00")


def test_get_category_detail_not_found(auth_client, test_breakdown_with_categories):
    """Test retrieving non-existent category."""
    response = auth_client.get(
        f"/api/v1/balance-breakdowns/{test_breakdown_with_categories.id}/categories/99999"
    )

    assert response.status_code == 404
    assert "detail" in response.json()


def test_get_breakdown_zero_balance(auth_client, db_session, test_account):
    """Test retrieving breakdown with zero balance."""
    breakdown = BalanceBreakdown(
        account_id=test_account.id,
        total_balance=Decimal("0.00"),
        snapshot_date=datetime.now(),
    )
    db_session.add(breakdown)
    db_session.commit()

    response = auth_client.get(f"/api/v1/balance-breakdowns/current?account_id={test_account.id}")

    assert response.status_code == 200
    data = response.json()

    assert Decimal(data["total_balance"]) == Decimal("0.00")
    assert len(data["categories"]) == 0


def test_category_ordering_by_display_rank(auth_client, db_session, test_account):
    """Test that categories are ordered by display_rank."""
    breakdown = BalanceBreakdown(
        account_id=test_account.id,
        total_balance=Decimal("3000.00"),
        snapshot_date=datetime.now(),
    )
    db_session.add(breakdown)
    db_session.flush()

    # Add categories with specific display_rank order
    categories = [
        BalanceCategory(
            breakdown_id=breakdown.id,
            category_name="Third",
            category_amount=Decimal("1000.00"),
            apr=Decimal("19.90"),
            display_rank=3,
        ),
        BalanceCategory(
            breakdown_id=breakdown.id,
            category_name="First",
            category_amount=Decimal("500.00"),
            apr=Decimal("19.90"),
            display_rank=1,
        ),
        BalanceCategory(
            breakdown_id=breakdown.id,
            category_name="Second",
            category_amount=Decimal("1500.00"),
            apr=Decimal("19.90"),
            display_rank=2,
        ),
    ]

    for cat in categories:
        db_session.add(cat)

    db_session.commit()

    response = auth_client.get(f"/api/v1/balance-breakdowns/current?account_id={test_account.id}")

    assert response.status_code == 200
    data = response.json()

    # Verify ordering
    assert data["categories"][0]["category_name"] == "First"
    assert data["categories"][1]["category_name"] == "Second"
    assert data["categories"][2]["category_name"] == "Third"


def test_get_breakdown_requires_auth(client, test_account):
    """Test that balance breakdown endpoints require authentication."""
    response = client.get(f"/api/v1/balance-breakdowns/current?account_id={test_account.id}")

    assert response.status_code == 401

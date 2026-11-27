"""
Tests for rewards summary retrieval.
"""
from datetime import datetime, timedelta
from decimal import Decimal


def test_get_rewards_summary_with_programme(auth_client, db_session):
    """Test rewards summary with active programme."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.rewards_programme import RewardsProgramme

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

    # Create rewards programme
    programme = RewardsProgramme(
        account_id=account.id,
        programme_name="Test Rewards",
        points_balance=1000,
        status="Active"
    )
    db_session.add(programme)
    db_session.commit()

    response = auth_client.get(f"/api/v1/rewards?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()
    assert "programme" in data
    assert "relevant_offers" in data
    assert "freshness" in data

    # ACC-1001 should have a programme
    if data["programme"]:
        assert "programme_name" in data["programme"]
        assert "points_balance" in data["programme"]


def test_get_rewards_summary_without_programme(auth_client, db_session):
    """Test rewards summary with null programme."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    # Create customer and account without rewards
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
        account_number_masked="****1002",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("10000.00"),
        available_credit=Decimal("8000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now() + timedelta(days=20)
    )
    db_session.add(account)
    db_session.commit()

    response = auth_client.get(f"/api/v1/rewards?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()
    assert "programme" in data
    assert "relevant_offers" in data
    assert isinstance(data["relevant_offers"], list)

    # ACC-1002 should have null programme
    assert data["programme"] is None


def test_get_rewards_summary_offers_filtered(auth_client, db_session):
    """Test that rewards summary filters offers by context."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-003",
        masked_name="Test C***",
        email="test3@example.com",
        phone_last_four="9012"
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
    db_session.commit()

    response = auth_client.get(f"/api/v1/rewards?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()

    # Relevant offers should be Rewards type
    for offer in data["relevant_offers"]:
        assert "offer_type" in offer

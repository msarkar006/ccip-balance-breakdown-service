"""
Tests for instalment plan endpoints.
"""
from decimal import Decimal


def test_list_instalment_plans_success(auth_client, db_session):
    """Test listing instalment plans for an account."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.instalment_plan import InstalmentPlan

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-TEST",
        masked_name="Test C***",
        email="test@example.com",
        phone_last_four="1234"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****9999",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
    )
    db_session.add(account)
    db_session.flush()

    # Create instalment plans
    plans_data = [
        {
            "plan_reference": "IP-TEST-1",
            "original_amount": Decimal("1200.00"),
            "remaining_balance": Decimal("800.00"),
            "instalment_count": 12,
            "monthly_payment": Decimal("100.00"),
            "apr": Decimal("9.90"),
            "status": "Active",
        },
        {
            "plan_reference": "IP-TEST-2",
            "original_amount": Decimal("600.00"),
            "remaining_balance": Decimal("200.00"),
            "instalment_count": 6,
            "monthly_payment": Decimal("100.00"),
            "apr": Decimal("0.00"),
            "status": "Active",
        },
    ]

    for plan_data in plans_data:
        plan = InstalmentPlan(account_id=account.id, **plan_data)
        db_session.add(plan)

    db_session.commit()

    # List instalment plans
    response = auth_client.get(
        "/api/v1/instalments",
        params={"account_id": account.id, "status": "Active"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "has_more" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["plan_reference"] in ["IP-TEST-1", "IP-TEST-2"]
    assert data["items"][0]["status"] == "Active"


def test_list_instalment_plans_pagination(auth_client, db_session):
    """Test pagination for instalment plans."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.instalment_plan import InstalmentPlan

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-TEST-2",
        masked_name="Test C***",
        email="test2@example.com",
        phone_last_four="5678"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****8888",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
    )
    db_session.add(account)
    db_session.flush()

    # Create 3 instalment plans
    for i in range(3):
        plan = InstalmentPlan(
            account_id=account.id,
            plan_reference=f"IP-PAGE-{i+1}",
            original_amount=Decimal("1000.00"),
            remaining_balance=Decimal("500.00"),
            instalment_count=10,
            monthly_payment=Decimal("100.00"),
            apr=Decimal("5.00"),
            status="Active",
        )
        db_session.add(plan)

    db_session.commit()

    # Request first page with limit=2
    response = auth_client.get(
        "/api/v1/instalments",
        params={"account_id": account.id, "limit": 2, "offset": 0}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["has_more"] is True

    # Request second page
    response = auth_client.get(
        "/api/v1/instalments",
        params={"account_id": account.id, "limit": 2, "offset": 2}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 1
    assert data["has_more"] is False


def test_get_instalment_plan_detail_with_linked_category(auth_client, db_session):
    """Test getting instalment plan detail with linked balance category."""
    from app.models.balance_breakdown import BalanceBreakdown
    from app.models.balance_category import BalanceCategory
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.instalment_plan import InstalmentPlan

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-TEST-3",
        masked_name="Test C***",
        email="test3@example.com",
        phone_last_four="9012"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****7777",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
    )
    db_session.add(account)
    db_session.flush()

    # Create instalment plan
    plan = InstalmentPlan(
        account_id=account.id,
        plan_reference="IP-DETAIL-1",
        original_amount=Decimal("1200.00"),
        remaining_balance=Decimal("800.00"),
        instalment_count=12,
        monthly_payment=Decimal("100.00"),
        apr=Decimal("9.90"),
        status="Active",
    )
    db_session.add(plan)
    db_session.flush()

    # Create balance breakdown with linked category
    from datetime import datetime

    breakdown = BalanceBreakdown(
        account_id=account.id,
        total_balance=Decimal("800.00"),
        snapshot_date=datetime.now(),
    )
    db_session.add(breakdown)
    db_session.flush()

    category = BalanceCategory(
        breakdown_id=breakdown.id,
        category_name="Instalment",
        category_amount=Decimal("800.00"),
        apr=Decimal("9.90"),
        source_instalment_plan_id=plan.id,
    )
    db_session.add(category)
    db_session.commit()

    # Get instalment plan detail
    response = auth_client.get(f"/api/v1/instalments/{plan.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == plan.id
    assert data["plan_reference"] == "IP-DETAIL-1"
    assert data["remaining_balance"] == "800.00"
    assert data["linked_category"] is not None
    assert data["linked_category"]["category_name"] == "Instalment"
    assert data["balance_effect"]["is_reflected_in_balance"] is True
    assert "total balance" in data["balance_effect"]["explanation"].lower()


def test_get_instalment_plan_detail_without_linked_category(auth_client, db_session):
    """Test getting instalment plan detail without linked balance category."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer
    from app.models.instalment_plan import InstalmentPlan

    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-TEST-4",
        masked_name="Test C***",
        email="test4@example.com",
        phone_last_four="3456"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****6666",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
    )
    db_session.add(account)
    db_session.flush()

    # Create instalment plan without linked category
    plan = InstalmentPlan(
        account_id=account.id,
        plan_reference="IP-DETAIL-2",
        original_amount=Decimal("600.00"),
        remaining_balance=Decimal("300.00"),
        instalment_count=6,
        monthly_payment=Decimal("100.00"),
        apr=Decimal("0.00"),
        status="Active",
    )
    db_session.add(plan)
    db_session.commit()

    # Get instalment plan detail
    response = auth_client.get(f"/api/v1/instalments/{plan.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == plan.id
    assert data["linked_category"] is None
    assert data["balance_effect"]["is_reflected_in_balance"] is False
    assert "not yet be reflected" in data["balance_effect"]["explanation"].lower()


def test_get_instalment_plan_detail_not_found(auth_client):
    """Test getting non-existent instalment plan."""
    response = auth_client.get("/api/v1/instalments/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_instalment_plans_empty(auth_client, db_session):
    """Test listing instalment plans with no results."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    # Create customer and account without plans
    customer = Customer(
        external_customer_id="CUST-TEST-5",
        masked_name="Test C***",
        email="test5@example.com",
        phone_last_four="7890"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****5555",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("5000.00"),
        current_balance=Decimal("0.00"),
        minimum_payment_due=Decimal("0.00"),
    )
    db_session.add(account)
    db_session.commit()

    # List instalment plans
    response = auth_client.get(
        "/api/v1/instalments",
        params={"account_id": account.id}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert len(data["items"]) == 0
    assert data["empty_state_message"] is not None
    assert "no active instalment plans" in data["empty_state_message"].lower()


def test_list_instalment_plans_requires_auth(client):
    """Test that listing instalment plans requires authentication."""
    response = client.get(
        "/api/v1/instalments",
        params={"account_id": 1}
    )

    assert response.status_code == 401

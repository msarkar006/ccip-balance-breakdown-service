"""
Tests for transaction endpoints - transaction history with pending/posted distinction.
"""
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.transaction import Transaction


def test_get_transactions_success(auth_client, db_session):
    """Test successful transaction list retrieval."""
    # Create test account (simple stub - in reality would use account factory)
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    customer = Customer(
        external_customer_id="TEST-CUST",
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
        payment_due_date=datetime.now() + timedelta(days=15)
    )
    db_session.add(account)
    db_session.flush()

    # Create test transactions
    transactions = [
        Transaction(
            account_id=account.id,
            external_transaction_id=f"TXN-TEST-{i}",
            transaction_date=datetime.now() - timedelta(days=i),
            posting_date=datetime.now() - timedelta(days=i-1) if i <= 3 else None,
            merchant_name=f"Merchant {i}",
            transaction_type="Purchase",
            amount=Decimal(f"{10 + i}.00"),
            currency="GBP",
            status="Posted" if i <= 3 else "Pending",
            description=f"Test transaction {i}"
        )
        for i in range(1, 6)
    ]
    for txn in transactions:
        db_session.add(txn)
    db_session.commit()

    # Request transactions
    response = auth_client.get(f"/api/v1/transactions?account_id={account.id}&limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "has_more" in data
    assert data["total"] == 5
    assert len(data["items"]) == 5
    assert data["has_more"] is False

    # Verify ordering (transaction_date DESC)
    for i in range(len(data["items"]) - 1):
        current_date = datetime.fromisoformat(data["items"][i]["transaction_date"].replace("Z", "+00:00"))
        next_date = datetime.fromisoformat(data["items"][i + 1]["transaction_date"].replace("Z", "+00:00"))
        assert current_date >= next_date


def test_get_transactions_pending_vs_posted(auth_client, db_session):
    """Test that pending and posted transactions are correctly distinguished."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    customer = Customer(
        external_customer_id="TEST-CUST-2",
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
        credit_limit=Decimal("3000.00"),
        available_credit=Decimal("2000.00"),
        current_balance=Decimal("1000.00"),
        minimum_payment_due=Decimal("50.00"),
        payment_due_date=datetime.now() + timedelta(days=10)
    )
    db_session.add(account)
    db_session.flush()

    # Posted transaction (has posting_date)
    posted_txn = Transaction(
        account_id=account.id,
        external_transaction_id="TXN-POSTED",
        transaction_date=datetime.now() - timedelta(days=3),
        posting_date=datetime.now() - timedelta(days=2),
        merchant_name="Posted Merchant",
        transaction_type="Purchase",
        amount=Decimal("50.00"),
        currency="GBP",
        status="Posted",
        description="Posted transaction"
    )
    db_session.add(posted_txn)

    # Pending transaction (no posting_date)
    pending_txn = Transaction(
        account_id=account.id,
        external_transaction_id="TXN-PENDING",
        transaction_date=datetime.now() - timedelta(hours=12),
        posting_date=None,
        merchant_name="Pending Merchant",
        transaction_type="Purchase",
        amount=Decimal("30.00"),
        currency="GBP",
        status="Pending",
        description="Pending transaction"
    )
    db_session.add(pending_txn)
    db_session.commit()

    response = auth_client.get(f"/api/v1/transactions?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 2

    # Find pending and posted transactions
    pending = next((t for t in data["items"] if t["status"] == "Pending"), None)
    posted = next((t for t in data["items"] if t["status"] == "Posted"), None)

    assert pending is not None
    assert posted is not None

    # Pending should have no posting_date
    assert pending["posting_date"] is None

    # Posted should have posting_date
    assert posted["posting_date"] is not None


def test_get_transactions_pagination(auth_client, db_session):
    """Test transaction pagination."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    customer = Customer(
        external_customer_id="TEST-CUST-3",
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
        credit_limit=Decimal("4000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("1000.00"),
        minimum_payment_due=Decimal("50.00"),
        payment_due_date=datetime.now() + timedelta(days=12)
    )
    db_session.add(account)
    db_session.flush()

    # Create 10 transactions
    for i in range(1, 11):
        txn = Transaction(
            account_id=account.id,
            external_transaction_id=f"TXN-PAGE-{i}",
            transaction_date=datetime.now() - timedelta(days=i),
            posting_date=datetime.now() - timedelta(days=i-1),
            merchant_name=f"Merchant {i}",
            transaction_type="Purchase",
            amount=Decimal(f"{i * 10}.00"),
            currency="GBP",
            status="Posted",
            description=f"Transaction {i}"
        )
        db_session.add(txn)
    db_session.commit()

    # First page
    response = auth_client.get(f"/api/v1/transactions?account_id={account.id}&limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 5
    assert data["total"] == 10
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert data["has_more"] is True

    # Second page
    response = auth_client.get(f"/api/v1/transactions?account_id={account.id}&limit=5&offset=5")
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 5
    assert data["total"] == 10
    assert data["limit"] == 5
    assert data["offset"] == 5
    assert data["has_more"] is False


def test_get_transactions_empty_state(auth_client, db_session):
    """Test empty state when no transactions exist."""
    from app.models.credit_card_account import CreditCardAccount
    from app.models.customer import Customer

    customer = Customer(
        external_customer_id="TEST-CUST-4",
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
        credit_limit=Decimal("2000.00"),
        available_credit=Decimal("2000.00"),
        current_balance=Decimal("0.00"),
        minimum_payment_due=Decimal("0.00"),
        payment_due_date=datetime.now() + timedelta(days=20)
    )
    db_session.add(account)
    db_session.commit()

    response = auth_client.get(f"/api/v1/transactions?account_id={account.id}")

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 0
    assert data["total"] == 0
    assert data["empty_state_message"] == "No transactions found for this account"


def test_get_transactions_requires_auth(client, db_session):
    """Test that transactions endpoint requires authentication."""
    response = client.get("/api/v1/transactions?account_id=1")
    assert response.status_code == 401

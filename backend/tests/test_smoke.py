"""
Smoke tests to validate basic database connectivity and model functionality.
"""
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import (
    AppUser,
    AuditLog,
    BalanceBreakdown,
    BalanceTransfer,
    CreditCard,
    CreditCardAccount,
    Customer,
    DirectDebitMandate,
    InstalmentPlan,
    Offer,
    Payee,
    Payment,
    RewardsProgramme,
    SynchronizationRecord,
    TrackingEvent,
    Transaction,
)


def test_database_connectivity(db_session: Session):
    """Test that database connection works."""
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_customer_model_crud(db_session: Session):
    """Test Customer model CRUD operations."""
    customer = Customer(
        external_customer_id="CUST-001",
        masked_name="John D***",
        email="john.doe@example.com",
        phone_last_four="1234"
    )
    db_session.add(customer)
    db_session.commit()

    retrieved = db_session.query(Customer).filter_by(external_customer_id="CUST-001").first()
    assert retrieved is not None
    assert retrieved.email == "john.doe@example.com"
    assert retrieved.id is not None


def test_app_user_model_crud(db_session: Session):
    """Test AppUser model with password hashing."""
    hashed = hash_password("test-password-123")
    user = AppUser(
        email="test@example.com",
        hashed_password=hashed,
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()

    retrieved = db_session.query(AppUser).filter_by(email="test@example.com").first()
    assert retrieved is not None
    assert retrieved.id is not None
    assert verify_password("test-password-123", retrieved.hashed_password)
    assert not verify_password("wrong-password", retrieved.hashed_password)


def test_credit_card_account_foreign_key(db_session: Session):
    """Test CreditCardAccount with foreign key to Customer."""
    customer = Customer(
        external_customer_id="CUST-002",
        masked_name="Jane S***",
        email="jane.smith@example.com",
        phone_last_four="5678"
    )
    db_session.add(customer)
    db_session.commit()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****1234",
        sort_code_masked="**-**-34",
        account_status="Active",
        credit_limit=5000.00,
        available_credit=3000.00,
        current_balance=2000.00,
        minimum_payment_due=50.00
    )
    db_session.add(account)
    db_session.commit()

    retrieved = db_session.query(CreditCardAccount).filter_by(customer_id=customer.id).first()
    assert retrieved is not None
    assert retrieved.current_balance == 2000.00


def test_all_models_instantiate(db_session: Session):
    """Test that all 20 models can be instantiated."""
    # Create customer first (required for FK relationships)
    customer = Customer(
        external_customer_id="CUST-003",
        masked_name="Test U***",
        email="test@example.com",
        phone_last_four="9999"
    )
    db_session.add(customer)
    db_session.commit()

    # Create account (required for many FK relationships)
    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****9999",
        sort_code_masked="**-**-99",
        account_status="Active",
        credit_limit=10000.00,
        available_credit=8000.00,
        current_balance=2000.00,
        minimum_payment_due=100.00
    )
    db_session.add(account)
    db_session.commit()

    # Test all models can be created
    models_to_test = [
        CreditCard(
            account_id=account.id,
            card_number_masked="****9999",
            card_type="Visa",
            card_status="Active",
            expiry_month=12,
            expiry_year=2026
        ),
        Transaction(
            account_id=account.id,
            external_transaction_id="TXN-001",
            transaction_date=datetime(2026, 11, 26, 10, 0, 0, tzinfo=timezone.utc),
            merchant_name="Test Merchant",
            transaction_type="Purchase",
            amount=100.00,
            currency="GBP",
            status="Posted"
        ),
        Payment(
            account_id=account.id,
            external_payment_id="PAY-001",
            payment_method="BankTransfer",
            amount=100.00,
            currency="GBP",
            status="Completed"
        ),
        BalanceTransfer(
            account_id=account.id,
            external_transfer_id="BT-001",
            transfer_amount=500.00,
            status="Completed"
        ),
        Payee(
            account_id=account.id,
            payee_name="Test Payee",
            account_number_masked="****1111",
            sort_code_masked="**-**-11",
            is_active=True
        ),
        DirectDebitMandate(
            account_id=account.id,
            mandate_reference="DD-001",
            mandate_type="FullBalance",
            status="Active"
        ),
        BalanceBreakdown(
            account_id=account.id,
            total_balance=2000.00,
            snapshot_date=datetime(2026, 11, 26, 0, 0, 0, tzinfo=timezone.utc)
        ),
        RewardsProgramme(
            account_id=account.id,
            programme_name="Cashback Plus",
            points_balance=1000,
            status="Active"
        ),
        Offer(
            account_id=account.id,
            offer_code="OFFER-001",
            offer_title="0% Balance Transfer",
            offer_type="BalanceTransfer",
            status="Active",
            valid_from=datetime(2026, 11, 1, 0, 0, 0, tzinfo=timezone.utc),
            valid_until=datetime(2027, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
        ),
        InstalmentPlan(
            account_id=account.id,
            plan_reference="PLAN-001",
            original_amount=1000.00,
            remaining_balance=800.00,
            instalment_count=12,
            monthly_payment=85.00,
            status="Active"
        ),
        TrackingEvent(
            entity_type="Payment",
            entity_id="PAY-001",
            event_type="Submitted",
            status="Processing"
        ),
        SynchronizationRecord(
            entity_type="Transaction",
            entity_id="TXN-001",
            sync_source="CoreBanking",
            sync_status="Completed"
        ),
        AuditLog(
            user_id=None,
            action="login_success",
            severity="INFO"
        )
    ]

    for model in models_to_test:
        db_session.add(model)

    db_session.commit()

    # Verify counts
    assert db_session.query(Customer).count() == 1
    assert db_session.query(CreditCardAccount).count() == 1
    assert db_session.query(CreditCard).count() == 1
    assert db_session.query(Transaction).count() == 1
    assert db_session.query(Payment).count() == 1
    assert db_session.query(TrackingEvent).count() == 1
    assert db_session.query(AuditLog).count() == 1


def test_user_id_is_integer_with_autoincrement(db_session: Session):
    """Verify AppUser.id is Integer with autoincrement."""
    user1 = AppUser(
        email="user1@example.com",
        hashed_password=hash_password("pass1"),
        is_active=True,
        is_superuser=False
    )
    user2 = AppUser(
        email="user2@example.com",
        hashed_password=hash_password("pass2"),
        is_active=True,
        is_superuser=False
    )
    db_session.add_all([user1, user2])
    db_session.commit()

    assert isinstance(user1.id, int)
    assert isinstance(user2.id, int)
    assert user2.id > user1.id

"""
Tests for support diagnostics lookup functionality.
"""
from datetime import datetime, timezone
from decimal import Decimal

from app.models.audit_log import AuditLog
from app.models.credit_card_account import CreditCardAccount
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.tracking_event import TrackingEvent


def test_diagnostic_lookup_account_success(auth_client, db_session):
    """Test diagnostic lookup for account entity with support user."""
    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-DIAG-001",
        masked_name="Test C***",
        email="test@example.com",
        phone_last_four="1234"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****9001",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now(timezone.utc),
    )
    db_session.add(account)
    db_session.commit()

    # Create support user and login
    from app.core.security import hash_password
    from app.models.app_user import AppUser

    support_user = AppUser(
        email="support_diag@example.com",
        hashed_password=hash_password("support123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(support_user)
    db_session.commit()

    # Login as support user
    response = auth_client.post("/api/v1/auth/login", json={
        "email": "support_diag@example.com",
        "password": "support123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    auth_client.headers["Authorization"] = f"Bearer {token}"

    # Perform diagnostic lookup
    response = auth_client.post("/api/v1/support-diagnostics/lookups", json={
        "verification_reference": "REF-001",
        "lookup_reason": "Customer inquiry about account status",
        "entity_type": "Account",
        "entity_id": str(account.id)
    })

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "lookup_id" in data
    assert "customer_visible_state" in data
    assert "lifecycle_events" in data
    assert "synchronization_summary" in data
    assert "escalation_context" in data

    # Verify customer-visible state
    state = data["customer_visible_state"]
    assert state["entity_type"] == "Account"
    assert state["account_number_masked"] == "****9001"
    assert state["account_status"] == "Active"

    # Verify audit log was created
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "support_lookup",
        AuditLog.user_id == support_user.id
    ).first()
    assert audit_log is not None
    assert audit_log.entity_type == "Account"


def test_diagnostic_lookup_payment_with_events(auth_client, db_session):
    """Test diagnostic lookup for payment entity with tracking events."""
    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-DIAG-002",
        masked_name="Test C***",
        email="test2@example.com",
        phone_last_four="5678"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****9002",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("10000.00"),
        available_credit=Decimal("7000.00"),
        current_balance=Decimal("3000.00"),
        minimum_payment_due=Decimal("150.00"),
        payment_due_date=datetime.now(timezone.utc),
    )
    db_session.add(account)
    db_session.flush()

    # Create payment
    payment = Payment(
        account_id=account.id,
        external_payment_id="PMT-TEST-001",
        payment_method="FasterPayments",
        amount=Decimal("100.00"),
        currency="GBP",
        status="Processing",
    )
    db_session.add(payment)
    db_session.flush()

    # Create tracking events
    event1 = TrackingEvent(
        entity_type="Payment",
        entity_id=str(payment.id),
        event_type="submitted",
        status="Submitted",
        event_data="Payment submitted for processing",
        occurred_at=datetime.now(timezone.utc)
    )
    event2 = TrackingEvent(
        entity_type="Payment",
        entity_id=str(payment.id),
        event_type="status_changed",
        status="Processing",
        event_data="Payment is being processed",
        occurred_at=datetime.now(timezone.utc)
    )
    db_session.add_all([event1, event2])
    db_session.commit()

    # Create support user and login
    from app.core.security import hash_password
    from app.models.app_user import AppUser

    support_user = AppUser(
        email="support_payment@example.com",
        hashed_password=hash_password("support123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(support_user)
    db_session.commit()

    # Login as support user
    response = auth_client.post("/api/v1/auth/login", json={
        "email": "support_payment@example.com",
        "password": "support123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    auth_client.headers["Authorization"] = f"Bearer {token}"

    # Perform diagnostic lookup
    response = auth_client.post("/api/v1/support-diagnostics/lookups", json={
        "verification_reference": "REF-002",
        "lookup_reason": "Customer inquiry about payment status",
        "entity_type": "Payment",
        "entity_id": str(payment.id)
    })

    assert response.status_code == 200
    data = response.json()

    # Verify lifecycle events
    events = data["lifecycle_events"]
    assert len(events) == 2
    assert events[0]["event_type"] == "submitted"
    assert events[1]["event_type"] == "status_changed"

    # Verify escalation context
    escalation = data["escalation_context"]
    assert escalation["recommended_route"] == "payment_operations"
    assert escalation["summary"] is not None


def test_diagnostic_lookup_forbidden_for_non_support(auth_client, db_session):
    """Test that non-support users get 403."""
    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-DIAG-003",
        masked_name="Test C***",
        email="test3@example.com",
        phone_last_four="9999"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****9003",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now(timezone.utc),
    )
    db_session.add(account)
    db_session.commit()

    # Use default auth_client (non-support user: tester@example.com)
    response = auth_client.post("/api/v1/support-diagnostics/lookups", json={
        "verification_reference": "REF-003",
        "lookup_reason": "Should be denied",
        "entity_type": "Account",
        "entity_id": str(account.id)
    })

    assert response.status_code == 403
    assert "support role required" in response.json()["detail"].lower()


def test_diagnostic_lookup_entity_not_found(auth_client, db_session):
    """Test diagnostic lookup for non-existent entity returns 404."""
    # Create support user and login
    from app.core.security import hash_password
    from app.models.app_user import AppUser

    support_user = AppUser(
        email="support_notfound@example.com",
        hashed_password=hash_password("support123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(support_user)
    db_session.commit()

    # Login as support user
    response = auth_client.post("/api/v1/auth/login", json={
        "email": "support_notfound@example.com",
        "password": "support123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    auth_client.headers["Authorization"] = f"Bearer {token}"

    # Attempt diagnostic lookup for non-existent account
    response = auth_client.post("/api/v1/support-diagnostics/lookups", json={
        "verification_reference": "REF-404",
        "lookup_reason": "Looking for non-existent entity",
        "entity_type": "Account",
        "entity_id": "999999"
    })

    assert response.status_code == 404


def test_diagnostic_lookup_audit_event_recorded(auth_client, db_session):
    """Test that diagnostic lookup records audit event before returning."""
    # Create customer and account
    customer = Customer(
        external_customer_id="CUST-DIAG-004",
        masked_name="Test C***",
        email="test4@example.com",
        phone_last_four="4444"
    )
    db_session.add(customer)
    db_session.flush()

    account = CreditCardAccount(
        customer_id=customer.id,
        account_number_masked="****9004",
        sort_code_masked="12-34-56",
        account_status="Active",
        credit_limit=Decimal("5000.00"),
        available_credit=Decimal("3000.00"),
        current_balance=Decimal("2000.00"),
        minimum_payment_due=Decimal("100.00"),
        payment_due_date=datetime.now(timezone.utc),
    )
    db_session.add(account)
    db_session.commit()

    # Create support user and login
    from app.core.security import hash_password
    from app.models.app_user import AppUser

    support_user = AppUser(
        email="support_audit@example.com",
        hashed_password=hash_password("support123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(support_user)
    db_session.commit()

    # Login as support user
    response = auth_client.post("/api/v1/auth/login", json={
        "email": "support_audit@example.com",
        "password": "support123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    auth_client.headers["Authorization"] = f"Bearer {token}"

    # Count existing audit logs
    initial_count = db_session.query(AuditLog).count()

    # Perform diagnostic lookup
    response = auth_client.post("/api/v1/support-diagnostics/lookups", json={
        "verification_reference": "REF-AUDIT",
        "lookup_reason": "Testing audit trail",
        "entity_type": "Account",
        "entity_id": str(account.id)
    })

    assert response.status_code == 200

    # Verify audit event was recorded
    final_count = db_session.query(AuditLog).count()
    assert final_count == initial_count + 1

    # Verify audit log details
    audit_log = db_session.query(AuditLog).order_by(AuditLog.id.desc()).first()
    assert audit_log.action == "support_lookup"
    assert audit_log.user_id == support_user.id
    assert audit_log.severity == "info"

    # Parse details JSON
    import json
    details = json.loads(audit_log.details)
    assert details["retention_class"] == "access_2y"
    assert details["verification_reference"] == "REF-AUDIT"

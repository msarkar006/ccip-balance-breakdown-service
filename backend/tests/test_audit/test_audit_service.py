"""
Tests for audit service.
"""
from datetime import datetime


def test_audit_service_record(db_session):
    """Test audit service record method creates audit log."""
    from app.audit.audit_service import AuditService

    service = AuditService(db_session)

    # Record audit event
    audit_log = service.record(
        user_id=1,
        action="login",
        entity_type="user",
        entity_id=1,
        severity="info",
        correlation_id="test-corr-123",
        details={"ip": "192.168.1.1"},
        ip_address="192.168.1.1",
        retention_class="access_2y"
    )

    # Verify created
    import json

    assert audit_log.id is not None
    assert audit_log.user_id == 1
    assert audit_log.action == "login"
    assert audit_log.entity_type == "user"
    assert audit_log.entity_id == "1"  # Converted to string
    assert audit_log.severity == "info"
    assert audit_log.correlation_id == "test-corr-123"
    details = json.loads(audit_log.details)
    assert details["retention_class"] == "access_2y"
    assert audit_log.ip_address == "192.168.1.1"
    assert audit_log.occurred_at is not None


def test_audit_service_financial_7y_retention(db_session):
    """Test audit service with financial_7y retention class."""
    from app.audit.audit_service import AuditService

    service = AuditService(db_session)

    # Record financial audit event
    audit_log = service.record(
        user_id=1,
        action="payment_initiation",
        entity_type="payment",
        entity_id=123,
        severity="info",
        details={"amount": 100.00},
        retention_class="financial_7y"
    )

    # Verify retention class in details
    import json
    details = json.loads(audit_log.details)
    assert details["retention_class"] == "financial_7y"


def test_audit_service_tracking_24m_retention(db_session):
    """Test audit service with tracking_24m retention class."""
    from app.audit.audit_service import AuditService

    service = AuditService(db_session)

    # Record tracking event
    audit_log = service.record(
        user_id=1,
        action="status_update",
        entity_type="payment",
        entity_id=456,
        severity="info",
        retention_class="tracking_24m"
    )

    # Verify retention class in details
    import json
    details = json.loads(audit_log.details)
    assert details["retention_class"] == "tracking_24m"


def test_audit_log_created_during_payment(auth_client, db_session):
    """Test that payment initiation creates audit log."""
    from datetime import timedelta
    from decimal import Decimal

    from app.models.audit_log import AuditLog
    from app.models.credit_card_account import CreditCardAccount

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****7001",
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

    # Perform step-up
    auth_client.post("/api/v1/auth/step-up", json={"password": "admin123"})

    # Count audit logs before
    initial_count = db_session.query(AuditLog).count()

    # Initiate payment
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "account_id": account.id,
            "amount": "100.00",
            "currency": "GBP",
            "payment_method": "BankTransfer",
            "scheduled_date": None,
            "idempotency_key": "audit-test-key-001"
        }
    )

    assert response.status_code == 201

    # Count audit logs after
    final_count = db_session.query(AuditLog).count()
    assert final_count > initial_count

    # Verify audit log details
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "payment_initiation"
    ).order_by(AuditLog.occurred_at.desc()).first()

    import json

    assert audit_log is not None
    assert audit_log.entity_type == "payment"
    details = json.loads(audit_log.details)
    assert details["retention_class"] == "financial_7y"


def test_audit_log_created_during_direct_debit_change(auth_client, db_session):
    """Test that direct debit change creates audit log."""
    from datetime import timedelta
    from decimal import Decimal

    from app.models.audit_log import AuditLog
    from app.models.credit_card_account import CreditCardAccount
    from app.models.direct_debit_mandate import DirectDebitMandate

    # Create test account
    account = CreditCardAccount(
        customer_id=1,
        account_number_masked="****7002",
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

    # Create mandate
    mandate = DirectDebitMandate(
        account_id=account.id,
        mandate_reference="DD-AUDIT-001",
        mandate_type="FixedAmount",
        payment_amount=Decimal("50.00"),
        status="Active",
        activated_at=datetime.now() - timedelta(days=60)
    )
    db_session.add(mandate)
    db_session.commit()

    # Perform step-up
    auth_client.post("/api/v1/auth/step-up", json={"password": "admin123"})

    # Count audit logs before
    initial_count = db_session.query(AuditLog).count()

    # Create change request
    response = auth_client.post(
        "/api/v1/direct-debits/change-requests",
        json={
            "mandate_id": mandate.id,
            "change_type": "Cancel",
            "new_payment_amount": None,
            "idempotency_key": "audit-dd-key-001"
        }
    )

    assert response.status_code == 201

    # Count audit logs after
    final_count = db_session.query(AuditLog).count()
    assert final_count > initial_count

    # Verify audit log details
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "direct_debit_change"
    ).order_by(AuditLog.occurred_at.desc()).first()

    import json

    assert audit_log is not None
    assert audit_log.entity_type == "direct_debit_change_request"
    details = json.loads(audit_log.details)
    assert details["retention_class"] == "financial_7y"

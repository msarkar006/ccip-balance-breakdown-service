from __future__ import annotations

from sqlalchemy import select

from app.models import AuditLog
from app.seed_data.users import PERSONAS
from tests.conftest import login


def _rows(db_session):
    db_session.expire_all()
    return db_session.scalars(select(AuditLog).order_by(AuditLog.occurred_at)).all()


def test_login_success_audit_with_correlation(seeded, client, db_session):
    p = PERSONAS["customer01"]
    cid = "corr-id-success-0001"
    r = client.post("/api/v1/auth/login", json={"username": p.username, "password": p.password},
                    headers={"X-Correlation-ID": cid})
    assert r.headers["X-Correlation-ID"] == cid
    row = _rows(db_session)[-1]
    assert (row.event_type, row.severity, row.correlation_id) == ("login_success", "info", cid)
    assert row.actor_user_id is not None


def test_login_failure_audit_is_committed_and_clean(seeded, client, db_session):
    p = PERSONAS["customer01"]
    cid = "corr-id-failure-0001"
    r = client.post("/api/v1/auth/login", json={"username": p.username, "password": "SecretWrong!1"},
                    headers={"X-Correlation-ID": cid})
    assert r.status_code == 401
    row = _rows(db_session)[-1]
    assert row.event_type == "login_failure" and row.correlation_id == cid
    blob = " ".join(str(v) for v in (row.detail, row.entity_id, row.entity_type))
    assert "SecretWrong" not in blob and "$2b$" not in blob


def test_unknown_user_failure_and_rate_limit_audited(seeded, client, db_session):
    for _ in range(6):
        client.post("/api/v1/auth/login", json={"username": "ghost", "password": "x"})
    rows = [r for r in _rows(db_session) if r.event_type == "login_failure"]
    assert len(rows) == 6
    assert rows[-1].severity == "warning" and rows[-1].actor_user_id is None


def test_logout_audit_and_no_token_leak(seeded, client, db_session):
    headers = login(client, "customer01")
    token = headers["Authorization"].split()[1]
    client.post("/api/v1/auth/logout", headers={**headers, "X-Correlation-ID": "corr-id-logout-0001"})
    row = _rows(db_session)[-1]
    assert row.event_type == "logout" and row.correlation_id == "corr-id-logout-0001"
    for entry in _rows(db_session):
        assert token not in " ".join(str(v) for v in (entry.detail, entry.entity_id))


def test_data_rights_audit_event_has_correlation(seeded, client, db_session):
    from sqlalchemy import select as _select

    from app.models import AuditLog as _AuditLog
    from tests.conftest import login as _login

    headers = {**_login(client), "Idempotency-Key": "audit-1", "X-Correlation-ID": "corr-dr-1"}
    created = client.post("/api/v1/data-rights-requests", json={"requestType": "export"}, headers=headers)
    assert created.status_code == 201
    row = db_session.scalars(_select(_AuditLog).where(_AuditLog.event_type == "data_rights_request_created")).one()
    assert row.correlation_id == "corr-dr-1"

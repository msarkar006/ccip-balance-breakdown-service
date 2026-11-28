from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models import UserSession
from tests.conftest import login


def test_logout_revokes_token(seeded, client, db_session):
    headers = login(client, "customer01")
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/session", headers=headers).status_code == 401
    row = db_session.scalars(select(UserSession)).one()
    assert row.revocation_reason == "logout" and row.revoked_at is not None


def test_inactivity_revokes_session(seeded, client, db_session):
    headers = login(client, "customer01")
    row = db_session.scalars(select(UserSession)).one()
    row.issued_at = datetime.now(UTC) - timedelta(minutes=30)
    row.last_activity_at = datetime.now(UTC) - timedelta(minutes=16)
    db_session.commit()
    response = client.get("/api/v1/auth/session", headers=headers)
    assert response.status_code == 401 and response.json() == {"detail": "Authentication required"}
    db_session.expire_all()
    row = db_session.scalars(select(UserSession)).one()
    assert row.revocation_reason == "inactivity" and row.revoked_at is not None


def test_activity_is_updated(seeded, client, db_session):
    headers = login(client, "customer01")
    row = db_session.scalars(select(UserSession)).one()
    row.issued_at = datetime.now(UTC) - timedelta(minutes=30)
    row.last_activity_at = datetime.now(UTC) - timedelta(minutes=10)
    db_session.commit()
    assert client.get("/api/v1/auth/session", headers=headers).status_code == 200
    db_session.expire_all()
    row = db_session.scalars(select(UserSession)).one()
    last = row.last_activity_at if row.last_activity_at.tzinfo else row.last_activity_at.replace(tzinfo=UTC)
    assert datetime.now(UTC) - last < timedelta(minutes=1)


def test_expired_session_is_401(seeded, client, db_session):
    headers = login(client, "customer01")
    row = db_session.scalars(select(UserSession)).one()
    row.issued_at = datetime.now(UTC) - timedelta(minutes=120)
    row.last_activity_at = datetime.now(UTC)
    row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()
    assert client.get("/api/v1/auth/session", headers=headers).status_code == 401

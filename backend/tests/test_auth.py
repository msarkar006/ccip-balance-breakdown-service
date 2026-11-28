from __future__ import annotations

from sqlalchemy import select

from app.models import AppUser, UserSession
from app.seed_data.users import PERSONAS
from tests.conftest import login


def _body(persona: str = "customer01", password: str | None = None) -> dict[str, str]:
    p = PERSONAS[persona]
    return {"username": p.username, "password": password or p.password}


def test_login_success_shape_and_no_leak(seeded, client, db_session):
    response = client.post("/api/v1/auth/login", json=_body())
    assert response.status_code == 200
    data = response.json()
    assert data["tokenType"] == "Bearer"
    assert data["inactivityTimeoutMinutes"] == 15
    assert data["user"]["username"] == "synthetic.customer01"
    assert data["user"]["role"] == "customer"
    assert data["user"]["customerId"]
    assert "password" not in response.text.lower().replace("passwordhash", "")
    assert "$2b$" not in response.text
    stored = db_session.scalars(select(UserSession)).all()
    assert len(stored) == 1
    assert stored[0].token_hash != data["accessToken"] and len(stored[0].token_hash) == 64
    user = db_session.scalar(select(AppUser).where(AppUser.username == "synthetic.customer01"))
    assert user is not None and user.last_login_at is not None


def test_login_failures_share_one_response(seeded, client):
    wrong = client.post("/api/v1/auth/login", json=_body(password="nope"))
    unknown = client.post("/api/v1/auth/login", json={"username": "nobody", "password": "nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_login_validation_422(seeded, client):
    assert client.post("/api/v1/auth/login", json={"username": "x"}).status_code == 422
    assert client.post("/api/v1/auth/login", json={**_body(), "extra": 1}).status_code == 422


def test_session_endpoint_and_requires_token(seeded, client):
    assert client.get("/api/v1/auth/session").status_code == 401
    headers = login(client, "admin01")
    response = client.get("/api/v1/auth/session", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["role"] == "administrator" and body["user"]["customerId"] is None
    assert {"issuedAt", "expiresAt", "lastActivityAt"} <= set(body)


def test_bad_tokens_are_401(seeded, client):
    for header in ("Bearer garbage", "Basic abc"):
        response = client.get("/api/v1/auth/session", headers={"Authorization": header})
        assert response.status_code == 401
        assert response.json() == {"detail": "Authentication required"}


def test_admin_gets_403_on_accounts(seeded, client):
    assert client.get("/api/v1/accounts", headers=login(client, "admin01")).status_code == 403


def test_inactive_user_cannot_login_or_continue(seeded, client, db_session):
    headers = login(client, "customer01")
    user = db_session.scalar(select(AppUser).where(AppUser.username == "synthetic.customer01"))
    user.is_active = False
    db_session.commit()
    assert client.get("/api/v1/auth/session", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/login", json=_body()).status_code == 401

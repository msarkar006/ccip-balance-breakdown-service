"""
Tests for authentication logout endpoint.
"""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user_session import UserSession


def test_logout_success(auth_client: TestClient, db_session: Session):
    """Test successful logout."""
    response = auth_client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "message" in data

    # Verify session was revoked
    sessions = db_session.query(UserSession).all()
    assert len(sessions) == 1
    assert sessions[0].revoked_at is not None


def test_logout_without_auth(client: TestClient):
    """Test logout without authentication."""
    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 401


def test_logout_twice(auth_client: TestClient, db_session: Session):
    """Test that logout can be called multiple times (idempotent)."""
    # First logout
    response1 = auth_client.post("/api/v1/auth/logout")
    assert response1.status_code == 200

    # Verify subsequent requests fail with 401 (session revoked)
    response2 = auth_client.post("/api/v1/auth/logout")
    assert response2.status_code == 401

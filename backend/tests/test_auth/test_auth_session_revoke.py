"""
Tests for session revocation endpoint.
"""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user_session import UserSession


def test_revoke_session_success(auth_client: TestClient, db_session: Session):
    """Test successful session revocation."""
    # Get current session ID
    me_response = auth_client.get("/api/v1/auth/me")
    session_id = me_response.json()["session_id"]

    # Revoke session
    response = auth_client.delete(f"/api/v1/auth/sessions/{session_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "message" in data

    # Verify session was revoked
    session = db_session.query(UserSession).filter(UserSession.id == session_id).first()
    assert session is not None
    assert session.revoked_at is not None


def test_revoke_nonexistent_session(auth_client: TestClient):
    """Test revoking a non-existent session."""
    response = auth_client.delete("/api/v1/auth/sessions/99999")

    assert response.status_code == 404


def test_revoke_session_without_auth(client: TestClient):
    """Test session revocation without authentication."""
    response = client.delete("/api/v1/auth/sessions/1")

    assert response.status_code == 401


def test_revoke_session_then_use_token(auth_client: TestClient, db_session: Session):
    """Test that using token after session revocation fails."""
    # Get current session ID
    me_response = auth_client.get("/api/v1/auth/me")
    session_id = me_response.json()["session_id"]

    # Revoke session
    revoke_response = auth_client.delete(f"/api/v1/auth/sessions/{session_id}")
    assert revoke_response.status_code == 200

    # Try to use the token again
    me_response2 = auth_client.get("/api/v1/auth/me")
    assert me_response2.status_code == 401

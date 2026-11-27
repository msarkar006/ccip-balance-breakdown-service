"""
Tests for get current user endpoint.
"""
from fastapi.testclient import TestClient


def test_get_me_success(auth_client: TestClient):
    """Test successful get current user."""
    response = auth_client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == "admin@example.com"
    assert data["is_active"] is True
    assert data["is_superuser"] is True
    assert "id" in data
    assert "session_id" in data
    assert "session_expires_at" in data


def test_get_me_without_auth(client: TestClient):
    """Test get current user without authentication."""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401

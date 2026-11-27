"""
Tests for step-up authentication endpoint.
"""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_step_up_success(auth_client: TestClient, db_session: Session):
    """Test successful step-up authentication."""
    response = auth_client.post(
        "/api/v1/auth/step-up",
        json={"password": "admin123"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "message" in data
    assert "valid_until" in data


def test_step_up_invalid_password(auth_client: TestClient):
    """Test step-up with invalid password."""
    response = auth_client.post(
        "/api/v1/auth/step-up",
        json={"password": "wrongpass"}
    )

    assert response.status_code == 401


def test_step_up_without_auth(client: TestClient):
    """Test step-up without authentication."""
    response = client.post(
        "/api/v1/auth/step-up",
        json={"password": "anypass"}
    )

    assert response.status_code == 401


def test_step_up_verification_stored(auth_client: TestClient, db_session: Session):
    """Test that step-up verification is stored in session."""
    # Get initial session state
    me_before = auth_client.get("/api/v1/auth/me")
    assert me_before.json()["step_up_verified_at"] is None

    # Perform step-up
    step_up_response = auth_client.post(
        "/api/v1/auth/step-up",
        json={"password": "admin123"}
    )
    assert step_up_response.status_code == 200

    # Check session state after step-up
    me_after = auth_client.get("/api/v1/auth/me")
    assert me_after.json()["step_up_verified_at"] is not None

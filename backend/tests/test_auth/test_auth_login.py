"""
Tests for authentication login endpoint.
"""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.app_user import AppUser


def test_login_success(client: TestClient, db_session: Session):
    """Test successful login."""
    # Create user
    user = AppUser(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpass123"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert "user" in data

    user_data = data["user"]
    assert user_data["email"] == "test@example.com"
    assert user_data["is_active"] is True
    assert user_data["is_superuser"] is False
    assert "session_id" in user_data


def test_login_invalid_credentials(client: TestClient, db_session: Session):
    """Test login with invalid credentials."""
    # Create user
    user = AppUser(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()

    # Login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpass"}
    )

    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "anypass123"}
    )

    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_inactive_user(client: TestClient, db_session: Session):
    """Test login with inactive user."""
    # Create inactive user
    user = AppUser(
        email="inactive@example.com",
        hashed_password=hash_password("testpass123"),
        is_active=False,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()

    # Attempt login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "testpass123"}
    )

    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


def test_login_validation_error(client: TestClient):
    """Test login with invalid request payload."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "short"}
    )

    assert response.status_code == 422

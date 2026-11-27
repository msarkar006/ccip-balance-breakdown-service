"""
Tests for operational summary endpoint.
"""


def test_operational_summary_default_window(auth_client, db_session):
    """Test operational summary with default 60-minute window."""
    # Create support user and login
    from app.core.security import hash_password
    from app.models.app_user import AppUser

    support_user = AppUser(
        email="support_ops@example.com",
        hashed_password=hash_password("support123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(support_user)
    db_session.commit()

    # Login as support user
    response = auth_client.post("/api/v1/auth/login", json={
        "email": "support_ops@example.com",
        "password": "support123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    auth_client.headers["Authorization"] = f"Bearer {token}"

    # Get operational summary
    response = auth_client.get("/api/v1/support-diagnostics/operational-summary")

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["window_minutes"] == 60
    assert "auth_failure_rate" in data
    assert "api_error_rate" in data
    assert "api_latency_p95" in data
    assert "stale_account_count" in data
    assert "invalid_synchronized_record_rate" in data
    assert "top_failure_categories" in data

    # Verify types
    assert isinstance(data["auth_failure_rate"], (int, float))
    assert isinstance(data["api_error_rate"], (int, float))
    assert isinstance(data["api_latency_p95"], (int, float))
    assert isinstance(data["stale_account_count"], int)
    assert isinstance(data["invalid_synchronized_record_rate"], (int, float))
    assert isinstance(data["top_failure_categories"], list)


def test_operational_summary_custom_window(auth_client, db_session):
    """Test operational summary with custom window."""
    # Create support user and login
    from app.core.security import hash_password
    from app.models.app_user import AppUser

    support_user = AppUser(
        email="support_ops2@example.com",
        hashed_password=hash_password("support123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(support_user)
    db_session.commit()

    # Login as support user
    response = auth_client.post("/api/v1/auth/login", json={
        "email": "support_ops2@example.com",
        "password": "support123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    auth_client.headers["Authorization"] = f"Bearer {token}"

    # Get operational summary with 120-minute window
    response = auth_client.get("/api/v1/support-diagnostics/operational-summary?window_minutes=120")

    assert response.status_code == 200
    data = response.json()
    assert data["window_minutes"] == 120


def test_operational_summary_no_pii(auth_client, db_session):
    """Test that operational summary contains no customer-identifying data."""
    # Create support user and login
    from app.core.security import hash_password
    from app.models.app_user import AppUser

    support_user = AppUser(
        email="support_ops3@example.com",
        hashed_password=hash_password("support123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(support_user)
    db_session.commit()

    # Login as support user
    response = auth_client.post("/api/v1/auth/login", json={
        "email": "support_ops3@example.com",
        "password": "support123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    auth_client.headers["Authorization"] = f"Bearer {token}"

    # Get operational summary
    response = auth_client.get("/api/v1/support-diagnostics/operational-summary")

    assert response.status_code == 200
    data = response.json()

    # Verify no customer-identifying fields
    response_str = str(data)

    # These should NOT appear in operational summary
    assert "customer_id" not in response_str.lower()
    assert "email" not in response_str.lower()
    assert "account_number" not in response_str.lower()
    assert "card_number" not in response_str.lower()


def test_operational_summary_forbidden_for_non_support(auth_client, db_session):
    """Test that non-support users cannot access operational summary."""
    # Use default auth_client (non-support user)
    response = auth_client.get("/api/v1/support-diagnostics/operational-summary")

    assert response.status_code == 403
    assert "support role required" in response.json()["detail"].lower()


def test_operational_summary_window_validation(auth_client, db_session):
    """Test operational summary window validation."""
    # Create support user and login
    from app.core.security import hash_password
    from app.models.app_user import AppUser

    support_user = AppUser(
        email="support_ops4@example.com",
        hashed_password=hash_password("support123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(support_user)
    db_session.commit()

    # Login as support user
    response = auth_client.post("/api/v1/auth/login", json={
        "email": "support_ops4@example.com",
        "password": "support123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    auth_client.headers["Authorization"] = f"Bearer {token}"

    # Test window < 5 (should fail)
    response = auth_client.get("/api/v1/support-diagnostics/operational-summary?window_minutes=4")
    assert response.status_code == 422

    # Test window > 1440 (should fail)
    response = auth_client.get("/api/v1/support-diagnostics/operational-summary?window_minutes=1441")
    assert response.status_code == 422

    # Test window = 5 (should succeed)
    response = auth_client.get("/api/v1/support-diagnostics/operational-summary?window_minutes=5")
    assert response.status_code == 200

    # Test window = 1440 (should succeed)
    response = auth_client.get("/api/v1/support-diagnostics/operational-summary?window_minutes=1440")
    assert response.status_code == 200

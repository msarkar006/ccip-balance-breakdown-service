"""
Tests for health endpoints (live and ready).
"""
from unittest.mock import patch


def test_health_live_always_ok(client):
    """Test health/live always returns 200 without authentication."""
    response = client.get("/api/health/live")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "checked_at" in data


def test_health_live_no_auth_required(client):
    """Test health/live does not require authentication."""
    # Clear any auth headers
    client.headers.clear()

    response = client.get("/api/health/live")
    assert response.status_code == 200


def test_health_ready_database_ok(client, db_session):
    """Test health/ready returns 200 when database is accessible."""
    response = client.get("/api/health/ready")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "checks" in data
    assert len(data["checks"]) > 0

    # Verify database check passed
    db_check = next((c for c in data["checks"] if c["component"] == "database"), None)
    assert db_check is not None
    assert db_check["status"] == "ok"


def test_health_ready_no_auth_required(client):
    """Test health/ready does not require authentication."""
    # Clear any auth headers
    client.headers.clear()

    response = client.get("/api/health/ready")
    # Should return 200 or 503, but not 401/403
    assert response.status_code in [200, 503]


def test_health_ready_database_unavailable(client, db_session):
    """Test health/ready returns 503 when database is unavailable."""
    # Mock database execute to raise an exception
    with patch.object(db_session, 'execute', side_effect=Exception("Database connection failed")):
        response = client.get("/api/health/ready")

        assert response.status_code == 503
        data = response.json()

        assert "detail" in data
        detail = data["detail"]
        assert detail["status"] == "unavailable"
        assert "checks" in detail

        # Verify database check failed
        db_check = next((c for c in detail["checks"] if c["component"] == "database"), None)
        assert db_check is not None
        assert db_check["status"] == "unavailable"
        assert "error" in db_check

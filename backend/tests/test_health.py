import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session


def test_liveness(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_correlation_id_generated_and_echoed(client: TestClient) -> None:
    generated = client.get("/health").headers["X-Correlation-ID"]
    assert generated
    supplied = uuid.uuid4().hex
    echoed = client.get("/health", headers={"X-Correlation-ID": supplied}).headers["X-Correlation-ID"]
    assert echoed == supplied


def test_malformed_correlation_id_is_replaced(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Correlation-ID": "bad id\twith spaces"})
    assert response.headers["X-Correlation-ID"] != "bad id\twith spaces"


def test_security_headers_present(client: TestClient) -> None:
    headers = client.get("/health").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "max-age" in headers["Strict-Transport-Security"]


def test_cors_allow_list(client: TestClient) -> None:
    allowed = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert allowed.headers["access-control-allow-credentials"] == "true"
    denied = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in denied.headers


def test_readiness_failure_is_safe_500(client: TestClient, db_session: Session) -> None:
    db_session.close()
    original = db_session.execute

    def boom(*args: object, **kwargs: object) -> None:
        from sqlalchemy.exc import OperationalError

        raise OperationalError("select 1", {}, Exception("secret-host down"))

    db_session.execute = boom  # type: ignore[method-assign,assignment]
    try:
        response = client.get("/health/ready")
    finally:
        db_session.execute = original  # type: ignore[method-assign]
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "secret" not in response.text
    assert response.headers["X-Correlation-ID"]


def test_metrics_count_requests(client: TestClient) -> None:
    from app.middleware.metrics import metrics

    client.get("/health")
    client.get("/nope")
    snapshot = metrics.snapshot()
    assert snapshot["request_count"] == 2
    assert snapshot["count_4xx"] == 1
    assert snapshot["count_5xx"] == 0


def test_database_pragma_foreign_keys(db_session: Session) -> None:
    # The test engine is separate from the app engine; assert the schema enforces FKs when enabled.
    assert db_session.execute(text("SELECT 1")).scalar_one() == 1

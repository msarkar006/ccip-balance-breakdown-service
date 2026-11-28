from fastapi.testclient import TestClient

from app.main import app

ALLOWED_OPERATIONS = {
    ("GET", "/health"),
    ("GET", "/health/ready"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
    ("GET", "/api/v1/auth/session"),
    ("GET", "/api/v1/accounts"),
    ("GET", "/api/v1/accounts/{account_id}"),
    ("GET", "/api/v1/accounts/{account_id}/cards"),
    ("GET", "/api/v1/accounts/{account_id}/balance-breakdowns"),
    ("GET", "/api/v1/balance-breakdowns/{breakdown_id}"),
    ("GET", "/api/v1/accounts/{account_id}/transactions"),
    ("GET", "/api/v1/transactions/{transaction_id}"),
    ("GET", "/api/v1/accounts/{account_id}/payments"),
    ("GET", "/api/v1/payments/{payment_id}"),
    ("GET", "/api/v1/accounts/{account_id}/tracking-events"),
    ("POST", "/api/v1/data-rights-requests"),
    ("GET", "/api/v1/data-rights-requests"),
    ("GET", "/api/v1/data-rights-requests/{request_id}"),
}


def _normalise(path: str) -> str:
    """Compare path shapes without caring about parameter names (accountId vs account_id)."""
    import re

    return re.sub(r"\{[^}]+\}", "{}", path)


def _operations() -> set[tuple[str, str]]:
    ops = set()
    for path, item in app.openapi()["paths"].items():
        for method in item:
            if method.lower() in {"get", "post", "put", "patch", "delete", "head", "options"}:
                ops.add((method.upper(), _normalise(path)))
    return ops


def test_allowed_list_has_eighteen_operations() -> None:
    assert len(ALLOWED_OPERATIONS) == 18


def test_no_operation_outside_the_allow_list() -> None:
    allowed = {(m, _normalise(p)) for m, p in ALLOWED_OPERATIONS}
    unexpected = _operations() - allowed
    assert not unexpected, f"routes outside the OpenAPI allow-list: {sorted(unexpected)}"


def test_only_allowed_writes_exist() -> None:
    writes = {op for op in _operations() if op[0] != "GET"}
    assert writes <= {
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/logout"),
        ("POST", "/api/v1/data-rights-requests"),
    }


def test_health_routes_registered_at_root() -> None:
    ops = _operations()
    assert ("GET", "/health") in ops
    assert ("GET", "/health/ready") in ops


def test_unlisted_methods_and_paths_get_safe_404(client: TestClient) -> None:
    for method, path in [
        ("POST", "/health"),
        ("DELETE", "/health"),
        ("PUT", "/api/v1/accounts"),
        ("POST", "/api/v1/payments"),
        ("PATCH", "/api/v1/accounts/1"),
        ("GET", "/api/v1/not-a-route"),
    ]:
        response = client.request(method, path)
        assert response.status_code == 404, (method, path)
        assert response.json() == {"detail": "Resource not found"}
        assert "allow" not in response.headers


def test_information_only_policy() -> None:
    import pytest

    from app.exceptions import InformationOnlyViolationError
    from app.policy import InformationOnlyPolicy

    InformationOnlyPolicy.assert_read_only("GET", "/api/v1/accounts")
    InformationOnlyPolicy.assert_read_only("POST", "/api/v1/auth/login")
    for method, path in [("POST", "/api/v1/payments"), ("DELETE", "/api/v1/accounts/1"), ("PUT", "/x")]:
        with pytest.raises(InformationOnlyViolationError):
            InformationOnlyPolicy.assert_read_only(method, path)

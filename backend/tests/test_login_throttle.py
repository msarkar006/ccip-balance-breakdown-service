from __future__ import annotations

from app.seed_data.users import PERSONAS


def _bad(client, name: str = "customer01"):
    return client.post("/api/v1/auth/login", json={"username": PERSONAS[name].username, "password": "wrong"})


def test_sixth_attempt_is_429_even_with_correct_password(seeded, client):
    for _ in range(5):
        assert _bad(client).status_code == 401
    good = client.post(
        "/api/v1/auth/login",
        json={"username": PERSONAS["customer01"].username, "password": PERSONAS["customer01"].password},
    )
    assert good.status_code == 429
    assert good.json() == {"detail": "Too many sign-in attempts"}
    assert int(good.headers["Retry-After"]) >= 1


def test_limiter_is_reset_between_tests(seeded, client):
    assert _bad(client).status_code == 401


def test_window_rolls_off():
    from app.services.login_rate_limiter import LoginRateLimiter

    now = [0.0]
    limiter = LoginRateLimiter(clock=lambda: now[0])
    for _ in range(5):
        limiter.record_failure("ip")
    assert limiter.is_limited("ip")
    now[0] = 15 * 60 + 1
    assert not limiter.is_limited("ip")

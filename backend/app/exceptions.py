"""Domain exceptions. Services raise these; central error handlers map them to safe HTTP responses."""

from __future__ import annotations


class DomainError(Exception):
    """Base class. `public_detail` is the only text ever shown to a client."""

    status_code = 500
    public_detail = "Internal server error"

    def __init__(self, internal_message: str | None = None) -> None:
        super().__init__(internal_message or self.public_detail)


class NotFoundError(DomainError):
    status_code = 404
    public_detail = "Resource not found"


class AuthenticationError(DomainError):
    status_code = 401
    public_detail = "Authentication required"


class ForbiddenError(DomainError):
    status_code = 403
    public_detail = "Not permitted"


class ValidationFailedError(DomainError):
    status_code = 422
    public_detail = "Request validation failed"


class TooManyRequestsError(DomainError):
    status_code = 429
    public_detail = "Too many requests"


class MaskingViolationError(DomainError):
    """A stored masked value does not carry the mask prefix; surfaces as a safe 500."""

    status_code = 500


class InformationOnlyViolationError(DomainError):
    """A request would create or imply a financial action."""

    status_code = 404
    public_detail = "Resource not found"


class AdapterNotEnabledError(DomainError):
    """An external adapter is inactive until an owner approves a read-only contract."""

    status_code = 503
    public_detail = "Service unavailable"


class RateLimitedError(TooManyRequestsError):
    """Login refused by the failure limiter; `retry_after` seconds go out as the Retry-After header."""

    public_detail = "Too many sign-in attempts"

    def __init__(self, retry_after: int, internal_message: str | None = None) -> None:
        super().__init__(internal_message)
        self.retry_after = max(1, int(retry_after))

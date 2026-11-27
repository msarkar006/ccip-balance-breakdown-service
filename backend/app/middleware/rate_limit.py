"""
Rate limiting middleware.
"""
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import RateLimitError
from app.core.settings import settings


class RateLimiter:
    """In-memory rate limiter for login endpoints."""

    def __init__(self):
        # Store: {identifier: [(timestamp1, timestamp2, ...)]}
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._window_seconds = 900  # 15 minutes
        self._max_attempts = 5

    def check_rate_limit(self, identifier: str) -> None:
        """
        Check if rate limit is exceeded for identifier.

        Args:
            identifier: Unique identifier (e.g., email or IP)

        Raises:
            RateLimitError: If rate limit exceeded
        """
        if not settings.rate_limit_enabled:
            return

        now = time.time()
        cutoff = now - self._window_seconds

        # Clean old attempts
        self._attempts[identifier] = [
            ts for ts in self._attempts[identifier] if ts > cutoff
        ]

        # Check limit
        if len(self._attempts[identifier]) >= self._max_attempts:
            raise RateLimitError(
                message=f"Too many attempts. Try again in {self._window_seconds // 60} minutes.",
                details={"identifier": identifier}
            )

        # Record attempt
        self._attempts[identifier].append(now)

    def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier (e.g., on successful login)."""
        if identifier in self._attempts:
            del self._attempts[identifier]


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply rate limiting to protected endpoints."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting check.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        # Rate limit only applies to login endpoint
        # (checked within the endpoint itself for better control)
        response = await call_next(request)
        return response

"""In-process rolling-window login failure counter, keyed by source IP (single-instance prototype)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

DEFAULT_MAX_FAILURES = 5
DEFAULT_WINDOW_SECONDS = 15 * 60


class LoginRateLimiter:
    def __init__(
        self,
        max_failures: int = DEFAULT_MAX_FAILURES,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str) -> deque[float]:
        queue = self._failures[key]
        cutoff = self._clock() - self.window_seconds
        while queue and queue[0] <= cutoff:
            queue.popleft()
        return queue

    def is_limited(self, key: str) -> bool:
        with self._lock:
            return len(self._prune(key)) >= self.max_failures

    def record_failure(self, key: str) -> None:
        with self._lock:
            self._prune(key).append(self._clock())

    def retry_after(self, key: str) -> int:
        with self._lock:
            queue = self._prune(key)
            if not queue:
                return 1
            return max(1, int(queue[0] + self.window_seconds - self._clock()) + 1)

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()


login_rate_limiter = LoginRateLimiter()

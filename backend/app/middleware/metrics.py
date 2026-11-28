"""Request metrics (pure ASGI): count, P95 latency and 4xx/5xx, with no sensitive labels."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("app.metrics")

SNAPSHOT_INTERVAL_SECONDS = 60.0
WINDOW_SIZE = 2000


class MetricsRegistry:
    """Thread-safe in-process registry. Labels are the route template and status class only."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self.request_count = 0
            self.client_errors = 0
            self.server_errors = 0
            self._durations: deque[float] = deque(maxlen=WINDOW_SIZE)
            self._last_snapshot = time.monotonic()

    def record(self, status: int, duration_ms: float) -> None:
        with self._lock:
            self.request_count += 1
            if 400 <= status < 500:
                self.client_errors += 1
            elif status >= 500:
                self.server_errors += 1
            self._durations.append(duration_ms)

    def p95_ms(self) -> float:
        with self._lock:
            data = sorted(self._durations)
        if not data:
            return 0.0
        return data[min(len(data) - 1, int(0.95 * len(data)))]

    def snapshot(self) -> dict[str, float | int]:
        return {
            "request_count": self.request_count,
            "p95_ms": round(self.p95_ms(), 2),
            "count_4xx": self.client_errors,
            "count_5xx": self.server_errors,
        }

    def maybe_emit(self) -> None:
        now = time.monotonic()
        with self._lock:
            if now - self._last_snapshot < SNAPSHOT_INTERVAL_SECONDS:
                return
            self._last_snapshot = now
        logger.info("metrics_snapshot %s", self.snapshot())


metrics = MetricsRegistry()


class MetricsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = time.perf_counter()
        status = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            metrics.record(status, (time.perf_counter() - started) * 1000.0)
            metrics.maybe_emit()

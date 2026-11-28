"""Synthetic tracking events and data-rights requests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# (account ref, entity type, entity source_ref or None for the account, fields)
TRACKING_EVENTS: list[tuple[str, str, str | None, dict[str, Any]]] = [
    (
        "ACC-1001",
        "account",
        None,
        {
            "lifecycle_status": "Open",
            "source_time": datetime(2026, 11, 20, 9, 0, tzinfo=UTC),
            "provenance": "synthetic seed",
            "occurred_at": datetime(2026, 11, 20, 9, 5, tzinfo=UTC),
        },
    ),
    (
        "ACC-1001",
        "transaction",
        "TXN-1",
        {
            "lifecycle_status": "Pending",
            "source_time": datetime(2026, 11, 22, 14, 5, tzinfo=UTC),
            "provenance": "synthetic seed",
            "occurred_at": datetime(2026, 11, 22, 14, 10, tzinfo=UTC),
        },
    ),
    (
        "ACC-1001",
        "payment",
        "PMT-1",
        {
            "lifecycle_status": "Processing",
            "source_time": None,
            "provenance": "synthetic seed",
            "occurred_at": datetime(2026, 11, 23, 8, 0, tzinfo=UTC),
        },
    ),
]

# (persona key, idempotency key, request_type, status, requested_at, due_at, completed_at, outcome)
DATA_RIGHTS: list[tuple[str, str, str, str, datetime, datetime, datetime | None, str | None]] = [
    (
        "customer01",
        "seed-export-received",
        "export",
        "received",
        datetime(2026, 11, 24, 10, 0, tzinfo=UTC),
        datetime(2026, 12, 24, 10, 0, tzinfo=UTC),
        None,
        None,
    ),
    (
        "customer01",
        "seed-export-fulfilled",
        "export",
        "fulfilled",
        datetime(2026, 10, 1, 10, 0, tzinfo=UTC),
        datetime(2026, 10, 31, 10, 0, tzinfo=UTC),
        datetime(2026, 10, 12, 15, 30, tzinfo=UTC),
        "Export prepared for the subject; no personal values are held in this summary.",
    ),
]

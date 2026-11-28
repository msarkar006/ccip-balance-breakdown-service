"""Freshness inputs: which approved setting governs which kind of timestamp."""

from __future__ import annotations

from typing import Literal

FreshnessKind = Literal["balance_breakdown", "transaction", "tracking_event"]

FRESHNESS_SETTING_KEYS: dict[str, str] = {
    "balance_breakdown": "freshness.max_age_seconds.balance_breakdown",
    "transaction": "freshness.max_age_seconds.transaction",
    "tracking_event": "freshness.max_age_seconds.tracking_event",
}

"""Synthetic cards (masked at rest; no full PAN exists anywhere)."""

from __future__ import annotations

from typing import Any

CARDS: list[tuple[str, dict[str, Any]]] = [
    (
        "ACC-1001",
        {
            "source_ref": "CRD-1",
            "masked_pan": "**** 4821",
            "card_status": "Active",
            "expiry_month_year": "2028-09",
            "is_digital": False,
        },
    ),
    (
        "ACC-1003",
        {
            "source_ref": "CRD-3",
            "masked_pan": "**** 9040",
            "card_status": "PendingActivation",
            "expiry_month_year": "2029-11",
            "is_digital": None,
        },
    ),
]

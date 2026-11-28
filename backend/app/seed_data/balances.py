"""Synthetic balance breakdowns from wireframe_03 (values copied, never computed)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

D = Decimal
AS_OF = datetime(2026, 11, 24, 8, 15, tzinfo=UTC)


def _cat(ref: str, rank: int, ctype: str, label: str, balance: str, apr: str, **extra: Any) -> dict[str, Any]:
    return {
        "source_ref": ref,
        "display_rank": rank,
        "category_type": ctype,
        "category_label": label,
        "category_balance": D(balance),
        "category_apr_percent": D(apr),
        **extra,
    }


# (account source_ref, breakdown fields, categories)
BREAKDOWNS: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = [
    (
        "ACC-1001",
        {
            "source_ref": "BBD-1",
            "as_of": AS_OF,
            "total_outstanding": D("4862.35"),
            "pending_total": D("114.20"),
            "is_zero_balance": False,
            "purchases_subtotal": D("1852.10"),
            "balance_transfers_subtotal": D("3010.25"),
        },
        [
            _cat("CAT-1", 1, "StandardPurchase", "Standard purchases", "1037.10", "22.9"),
            _cat(
                "CAT-2", 2, "PromotionalPurchase", "Purchase promotion", "612.00", "0",
                promo_end_date=date(2027, 3, 14), revert_rate_percent=D("22.9"), days_to_expiry=110,
            ),
            _cat(
                "CAT-3", 3, "BalanceTransfer", "Balance transfer 1", "1800.00", "0",
                promo_end_date=date(2027, 6, 30), revert_rate_percent=D("22.9"), days_to_expiry=218,
                source_balance_transfer_ref="BT-1",
            ),
            _cat(
                "CAT-4", 4, "BalanceTransfer", "Balance transfer 2", "1210.25", "2.9",
                promo_end_date=date(2028, 1, 15), revert_rate_percent=D("22.9"), days_to_expiry=417,
                source_balance_transfer_ref="BT-2",
            ),
            _cat(
                "CAT-5", 5, "Instalment", "Instalment plan IP-66", "203.00", "0",
                source_instalment_plan_ref="IP-66",
            ),
        ],
    ),
    (
        "ACC-1002",
        {
            "source_ref": "BBD-2",
            "as_of": AS_OF,
            "total_outstanding": D("0.00"),
            "pending_total": D("4.80"),
            "is_zero_balance": True,
        },
        [],
    ),
    (
        # Source time missing: exercises `freshness unavailable` and null-last ordering.
        "ACC-1003",
        {
            "source_ref": "BBD-3",
            "as_of": None,
            "total_outstanding": D("7400.55"),
            "pending_total": D("0.00"),
            "is_zero_balance": False,
        },
        [
            _cat("CAT-6", 1, "StandardPurchase", "Standard purchases", "7400.55", "22.9"),
        ],
    ),
]

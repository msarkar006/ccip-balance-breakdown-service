"""Synthetic transactions from wireframe_04. ACC-1002 deliberately has none."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

# (account source_ref, card source_ref or None, fields)
TRANSACTIONS: list[tuple[str, str | None, dict[str, Any]]] = [
    (
        "ACC-1001",
        "CRD-1",
        {
            "source_ref": "TXN-1",
            "transaction_status": "Pending",
            "transaction_time": datetime(2026, 11, 22, 14, 5, tzinfo=UTC),
            "posted_date": None,
            "transaction_amount": Decimal("42.15"),
            "merchant_name": "TESCO STORES 4412",
            "merchant_category_code": "5411",
            "eligible_for_instalment": False,
        },
    ),
    (
        "ACC-1001",
        "CRD-1",
        {
            "source_ref": "TXN-2",
            "transaction_status": "Pending",
            "transaction_time": datetime(2026, 11, 22, 9, 40, tzinfo=UTC),
            "posted_date": None,
            "transaction_amount": Decimal("31.00"),
            "merchant_name": "TRAINLINE LONDON",
            "merchant_category_code": "4112",
            "eligible_for_instalment": False,
        },
    ),
    (
        "ACC-1001",
        "CRD-1",
        {
            "source_ref": "TXN-3",
            "transaction_status": "Posted",
            "transaction_time": datetime(2026, 11, 20, 12, 0, tzinfo=UTC),
            "posted_date": date(2026, 11, 21),
            "transaction_amount": Decimal("20.00"),
            "merchant_name": "Example merchant",
            "merchant_category_code": "5999",
            "eligible_for_instalment": False,
        },
    ),
    (
        "ACC-1001",
        "CRD-1",
        {
            "source_ref": "TXN-4",
            "transaction_status": "Posted",
            "transaction_time": datetime(2026, 11, 18, 16, 30, tzinfo=UTC),
            "posted_date": date(2026, 11, 19),
            "transaction_amount": Decimal("640.00"),
            "merchant_name": "Example electronics",
            "merchant_category_code": "5732",
            "eligible_for_instalment": True,
        },
    ),
]

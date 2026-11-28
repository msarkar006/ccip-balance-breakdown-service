"""Synthetic payments from wireframe_05. ACC-1002 deliberately has none."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

_NW = "Nationwide Current Account"


def _p(
    ref: str,
    ptype: str,
    status: str,
    amount: str,
    when: date,
    method: str,
    bank: str,
    mandate: str | None = None,
) -> tuple[str, dict[str, Any]]:
    return (
        "ACC-1001",
        {
            "source_ref": ref,
            "payment_type": ptype,
            "payment_method": method,
            "payment_status": status,
            "payment_amount": Decimal(amount),
            "payment_date": when,
            "via_mandate_ref": mandate,
            "source_bank_name": bank,
            "source_masked_account": "****1234",
        },
    )


# (account source_ref, fields)
PAYMENTS: list[tuple[str, dict[str, Any]]] = [
    _p("PMT-1", "OneOff", "Completed", "500.00", date(2026, 11, 24), "FasterPayments", _NW),
    _p("PMT-2", "OneOff", "Processing", "121.56", date(2026, 11, 24), "DebitCard", _NW),
    _p("PMT-3", "OneOff", "Failed", "2000.00", date(2026, 11, 23), "FasterPayments", "Other Bank Ltd"),
    _p("PMT-4", "Scheduled", "Submitted", "300.00", date(2026, 12, 15), "FasterPayments", _NW),
    _p("PMT-5", "Scheduled", "Cancelled", "100.00", date(2026, 11, 30), "FasterPayments", _NW),
    _p("PMT-6", "DirectDebitCollection", "Completed", "121.56", date(2026, 10, 30), "DirectDebit", _NW, "MND-1"),
]

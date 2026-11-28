"""Synthetic account records. Fixed values; no real data."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

CUSTOMERS: dict[str, dict[str, Any]] = {
    "customer01": {"source_ref": "CUS-1001", "customer_since": date(2021, 3, 18), "marketing_consent": False},
    "customer02": {"source_ref": "CUS-2001", "customer_since": date(2022, 6, 1), "marketing_consent": False},
}

# (persona key, account fields)
ACCOUNTS: list[tuple[str, dict[str, Any]]] = [
    (
        "customer01",
        {
            "source_ref": "ACC-1001",
            "product_name": "Synthetic Everyday Card",
            "account_status": "Open",
            "opened_on": date(2021, 3, 18),
            "currency": "GBP",
            "credit_limit": Decimal("10000.00"),
            "available_credit": Decimal("5137.65"),
            "current_balance": Decimal("4862.35"),
            "standard_purchase_apr": Decimal("22.900"),
            "last_statement_balance": Decimal("4701.10"),
            "next_statement_date": date(2026, 12, 5),
            "payment_due_date": date(2026, 12, 30),
            "minimum_payment": Decimal("121.56"),
        },
    ),
    (
        "customer01",
        {
            "source_ref": "ACC-1002",
            "product_name": "Synthetic Zero Balance Card",
            "account_status": "Open",
            "opened_on": date(2022, 8, 9),
            "currency": "GBP",
            "credit_limit": Decimal("3000.00"),
            "available_credit": Decimal("3000.00"),
            "current_balance": Decimal("0.00"),
            "standard_purchase_apr": Decimal("19.900"),
            "last_statement_balance": Decimal("0.00"),
            "next_statement_date": date(2026, 12, 12),
            "payment_due_date": None,
            "minimum_payment": None,
        },
    ),
    (
        "customer01",
        {
            "source_ref": "ACC-1003",
            "product_name": "Synthetic New Card",
            "account_status": "Open",
            "opened_on": date(2026, 1, 20),
            "currency": "GBP",
            "credit_limit": Decimal("1500.00"),
            "available_credit": None,
            "current_balance": None,
            "standard_purchase_apr": None,
            "last_statement_balance": None,
            "next_statement_date": None,
            "payment_due_date": None,
            "minimum_payment": None,
        },
    ),
    (
        "customer02",
        {
            "source_ref": "ACC-2001",
            "product_name": "Synthetic Other Customer Card",
            "account_status": "Open",
            "opened_on": date(2022, 6, 1),
            "currency": "GBP",
            "credit_limit": Decimal("2000.00"),
            "available_credit": Decimal("1500.00"),
            "current_balance": Decimal("500.00"),
            "standard_purchase_apr": Decimal("21.900"),
            "last_statement_balance": Decimal("450.00"),
            "next_statement_date": date(2026, 12, 8),
            "payment_due_date": date(2026, 12, 31),
            "minimum_payment": Decimal("25.00"),
        },
    ),
]

"""Inactive external adapter stubs. Read-only; enabled only after an owner approves a contract."""

from __future__ import annotations

from abc import ABC
from typing import NoReturn

from app.exceptions import AdapterNotEnabledError


class ExternalAdapter(ABC):  # noqa: B024 - marker base; concrete adapters stay inactive
    """Base for future read-only source adapters. Every call refuses until a contract is approved."""

    name = "external"
    enabled = False

    def _refuse(self) -> NoReturn:
        raise AdapterNotEnabledError(f"adapter '{self.name}' is not enabled: no approved owner contract")

    def fetch(self, reference: str) -> NoReturn:
        """Read one record by source reference (read-only)."""
        self._refuse()

    def fetch_page(self, account_reference: str, limit: int, offset: int) -> NoReturn:
        """Read a page of records for an account (read-only)."""
        self._refuse()


class AccountSourceAdapter(ExternalAdapter):
    name = "account-source"


class BalanceSourceAdapter(ExternalAdapter):
    name = "balance-source"


class TransactionSourceAdapter(ExternalAdapter):
    name = "transaction-source"


class PaymentSourceAdapter(ExternalAdapter):
    name = "payment-source"

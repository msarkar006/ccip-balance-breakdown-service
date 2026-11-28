"""Model factories: one per table, built with the real field names. Each adds and flushes."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import lru_cache

import bcrypt
from sqlalchemy.orm import Session

from app.models import (
    Account,
    AppUser,
    AuditLog,
    BalanceBreakdown,
    BalanceCategory,
    Card,
    Customer,
    DataRightsRequest,
    Payment,
    TrackingEvent,
    Transaction,
    UserSession,
)
from app.seed_data.users import PERSONAS

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


@lru_cache(maxsize=4)
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def _add(db: Session, obj):  # type: ignore[no-untyped-def]
    db.add(obj)
    db.flush()
    return obj


def make_customer(db: Session, **kw) -> Customer:  # type: ignore[no-untyped-def]
    return _add(db, Customer(**{"source_ref": f"CUS-{uuid.uuid4().hex[:8]}", **kw}))


def make_user(db: Session, *, customer: Customer | None = None, persona: str | None = None, **kw) -> AppUser:  # type: ignore[no-untyped-def]
    p = PERSONAS[persona or "customer01"]
    role = kw.pop("role", p.role)
    if role == "customer" and customer is None:
        customer = make_customer(db)
    values = {
        "username": f"{p.username}.{uuid.uuid4().hex[:6]}" if persona is None else p.username,
        "password_hash": hash_password(p.password),
        "role": role,
        "is_active": True,
        "customer_id": customer.id if customer else None,
    }
    values.update(kw)
    return _add(db, AppUser(**values))


def make_session(db: Session, user: AppUser, **kw) -> UserSession:  # type: ignore[no-untyped-def]
    values = {
        "user_id": user.id,
        "token_hash": uuid.uuid4().hex + uuid.uuid4().hex,
        "issued_at": NOW,
        "expires_at": NOW + timedelta(minutes=60),
        "last_activity_at": NOW,
    }
    values.update(kw)
    return _add(db, UserSession(**values))


def make_account(db: Session, customer: Customer, **kw) -> Account:  # type: ignore[no-untyped-def]
    values = {
        "customer_id": customer.id,
        "source_ref": f"ACC-{uuid.uuid4().hex[:8]}",
        "product_name": "Synthetic Credit Card",
        "account_status": "Open",
        "currency": "GBP",
        "credit_limit": Decimal("5000.00"),
        "current_balance": Decimal("1200.00"),
    }
    values.update(kw)
    return _add(db, Account(**values))


def make_card(db: Session, account: Account, **kw) -> Card:  # type: ignore[no-untyped-def]
    values = {"account_id": account.id, "masked_pan": "**** 4821", "card_status": "Active"}
    values.update(kw)
    return _add(db, Card(**values))


def make_breakdown(db: Session, account: Account, **kw) -> BalanceBreakdown:  # type: ignore[no-untyped-def]
    values = {"account_id": account.id, "as_of": NOW, "total_outstanding": Decimal("1200.00")}
    values.update(kw)
    return _add(db, BalanceBreakdown(**values))


def make_category(db: Session, breakdown: BalanceBreakdown, **kw) -> BalanceCategory:  # type: ignore[no-untyped-def]
    values = {
        "breakdown_id": breakdown.id,
        "category_type": "StandardPurchase",
        "category_label": "Standard purchases",
        "display_rank": 1,
    }
    values.update(kw)
    return _add(db, BalanceCategory(**values))


def make_transaction(db: Session, account: Account, **kw) -> Transaction:  # type: ignore[no-untyped-def]
    values = {
        "account_id": account.id,
        "transaction_status": "Posted",
        "transaction_time": NOW,
        "transaction_amount": Decimal("12.50"),
    }
    values.update(kw)
    return _add(db, Transaction(**values))


def make_payment(db: Session, account: Account, **kw) -> Payment:  # type: ignore[no-untyped-def]
    values = {
        "account_id": account.id,
        "payment_type": "OneOff",
        "payment_method": "FasterPayments",
        "payment_status": "Completed",
        "payment_amount": Decimal("100.00"),
        "payment_date": date(2026, 1, 10),
        "source_masked_account": "****1234",
    }
    values.update(kw)
    return _add(db, Payment(**values))


def make_tracking_event(db: Session, account: Account, **kw) -> TrackingEvent:  # type: ignore[no-untyped-def]
    values = {
        "account_id": account.id,
        "tracked_entity_type": "account",
        "tracked_entity_id": account.id,
        "lifecycle_status": "Open",
        "provenance": "synthetic seed",
    }
    values.update(kw)
    return _add(db, TrackingEvent(**values))


def make_audit_entry(db: Session, **kw) -> AuditLog:  # type: ignore[no-untyped-def]
    values = {
        "severity": "info",
        "event_type": "login_success",
        "entity_type": "app_user",
        "correlation_id": uuid.uuid4().hex,
    }
    values.update(kw)
    return _add(db, AuditLog(**values))


def make_data_rights_request(db: Session, **kw) -> DataRightsRequest:  # type: ignore[no-untyped-def]
    values = {
        "subject_ref": "CUS-1",
        "request_type": "export",
        "idempotency_key": uuid.uuid4().hex,
        "requested_at": NOW,
        "due_at": NOW + timedelta(days=30),
    }
    values.update(kw)
    return _add(db, DataRightsRequest(**values))

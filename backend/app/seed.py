"""Idempotent synthetic seed. Run as `python -m app.seed`; gated by SEED_ENABLED."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    Account,
    AppUser,
    BalanceBreakdown,
    BalanceCategory,
    Card,
    Customer,
    DataRightsRequest,
    Payment,
    TrackingEvent,
    Transaction,
)
from app.seed_data.accounts import ACCOUNTS, CUSTOMERS
from app.seed_data.balances import BREAKDOWNS
from app.seed_data.cards import CARDS
from app.seed_data.payments import PAYMENTS
from app.seed_data.tracking import DATA_RIGHTS, TRACKING_EVENTS
from app.seed_data.transactions import TRANSACTIONS
from app.seed_data.users import PERSONAS
from app.services.auth_service import hash_password

logger = logging.getLogger("app.seed")


def seed_database(db: Session) -> None:
    """Insert missing synthetic rows; existing rows are left untouched."""
    customers: dict[str, Customer] = {}
    for key, values in CUSTOMERS.items():
        row = db.scalar(select(Customer).where(Customer.source_ref == values["source_ref"]))
        if row is None:
            row = Customer(**values)
            db.add(row)
            db.flush()
        customers[key] = row

    for persona in PERSONAS.values():
        if db.scalar(select(AppUser.id).where(AppUser.username == persona.username)) is None:
            customer = customers.get(persona.key)
            db.add(
                AppUser(
                    username=persona.username,
                    password_hash=hash_password(persona.password),
                    role=persona.role,
                    is_active=True,
                    customer_id=customer.id if persona.role == "customer" and customer else None,
                )
            )

    for key, values in ACCOUNTS:
        if db.scalar(select(Account.id).where(Account.source_ref == values["source_ref"])) is None:
            db.add(Account(customer_id=customers[key].id, **values))
    db.flush()

    for account_ref, values in CARDS:
        account_id = db.scalar(select(Account.id).where(Account.source_ref == account_ref))
        if account_id is not None and db.scalar(select(Card.id).where(Card.source_ref == values["source_ref"])) is None:
            db.add(Card(account_id=account_id, **values))
    db.flush()

    for account_ref, values, categories in BREAKDOWNS:
        account_id = db.scalar(select(Account.id).where(Account.source_ref == account_ref))
        if account_id is None:
            continue
        breakdown = db.scalar(select(BalanceBreakdown).where(BalanceBreakdown.source_ref == values["source_ref"]))
        if breakdown is None:
            breakdown = BalanceBreakdown(account_id=account_id, **values)
            db.add(breakdown)
            db.flush()
        for cat in categories:
            if db.scalar(select(BalanceCategory.id).where(BalanceCategory.source_ref == cat["source_ref"])) is None:
                db.add(BalanceCategory(breakdown_id=breakdown.id, **cat))
    db.flush()

    for account_ref, card_ref, values in TRANSACTIONS:
        account_id = db.scalar(select(Account.id).where(Account.source_ref == account_ref))
        if account_id is None:
            continue
        if db.scalar(select(Transaction.id).where(Transaction.source_ref == values["source_ref"])) is None:
            card_id = db.scalar(select(Card.id).where(Card.source_ref == card_ref)) if card_ref else None
            db.add(Transaction(account_id=account_id, card_id=card_id, **values))
    db.flush()

    for account_ref, values in PAYMENTS:
        account_id = db.scalar(select(Account.id).where(Account.source_ref == account_ref))
        if account_id is None:
            continue
        if db.scalar(select(Payment.id).where(Payment.source_ref == values["source_ref"])) is None:
            db.add(Payment(account_id=account_id, **values))
    db.flush()

    _seed_tracking(db)
    _seed_data_rights(db, customers)
    db.flush()


def _seed_tracking(db: Session) -> None:
    for account_ref, entity_type, entity_ref, values in TRACKING_EVENTS:
        account_id = db.scalar(select(Account.id).where(Account.source_ref == account_ref))
        if account_id is None:
            continue
        transaction_id = payment_id = None
        entity_id: uuid.UUID | None = account_id
        if entity_type == "transaction":
            transaction_id = entity_id = db.scalar(select(Transaction.id).where(Transaction.source_ref == entity_ref))
        elif entity_type == "payment":
            payment_id = entity_id = db.scalar(select(Payment.id).where(Payment.source_ref == entity_ref))
        if entity_id is None:
            continue
        exists = db.scalar(
            select(TrackingEvent.id).where(
                TrackingEvent.tracked_entity_id == entity_id,
                TrackingEvent.lifecycle_status == values["lifecycle_status"],
            )
        )
        if exists is None:
            db.add(
                TrackingEvent(
                    account_id=account_id,
                    transaction_id=transaction_id,
                    payment_id=payment_id,
                    tracked_entity_type=entity_type,
                    tracked_entity_id=entity_id,
                    **values,
                )
            )


def _seed_data_rights(db: Session, customers: dict[str, Customer]) -> None:
    for key, idem, rtype, status, requested_at, due_at, completed_at, outcome in DATA_RIGHTS:
        user = db.scalar(select(AppUser).where(AppUser.username == PERSONAS[key].username))
        customer = customers.get(key)
        if user is None or customer is None:
            continue
        if db.scalar(
            select(DataRightsRequest.id).where(
                DataRightsRequest.requested_by_user_id == user.id, DataRightsRequest.idempotency_key == idem
            )
        ):
            continue
        db.add(
            DataRightsRequest(
                subject_customer_id=customer.id,
                subject_ref=customer.source_ref,
                requested_by_user_id=user.id,
                request_type=rtype,
                status=status,
                idempotency_key=idem,
                requested_at=requested_at,
                due_at=due_at,
                completed_at=completed_at,
                outcome_summary=outcome,
            )
        )


def main() -> None:
    from app.database import get_session_factory

    if not get_settings().seed_enabled:
        logger.info("SEED_ENABLED is false; seed skipped")
        return
    with get_session_factory()() as session:
        seed_database(session)
        session.commit()
    logger.info("seed complete")


if __name__ == "__main__":
    main()

import os
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.database import Base
from app.exceptions import AdapterNotEnabledError, MaskingViolationError
from tests import factories
from tests.conftest import _BACKEND

EXPECTED_TABLES = {
    "customers",
    "app_users",
    "user_sessions",
    "accounts",
    "cards",
    "balance_breakdowns",
    "balance_categories",
    "transactions",
    "payments",
    "tracking_events",
    "audit_log",
    "data_rights_requests",
    "app_settings",
}


@pytest.fixture
def migrated_url(tmp_path: Path) -> str:
    url = f"sqlite:///{(tmp_path / 'm.db').as_posix()}"
    config = Config(str(_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    return url


def test_migration_creates_all_tables_and_matches_models(migrated_url: str) -> None:
    engine = create_engine(migrated_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names()) - {"alembic_version"}
    assert tables == EXPECTED_TABLES == set(Base.metadata.tables)
    for name, table in Base.metadata.tables.items():
        assert {c["name"] for c in inspector.get_columns(name)} == {c.name for c in table.columns}, name
        model_indexes = {i.name for i in table.indexes}
        db_indexes = {i["name"] for i in inspector.get_indexes(name) if not str(i["name"]).startswith("sqlite_")}
        assert model_indexes <= db_indexes, name
    engine.dispose()


def test_single_migration_lineage() -> None:
    from alembic.script import ScriptDirectory

    config = Config(str(_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND / "alembic"))
    script = ScriptDirectory.from_config(config)
    assert len(script.get_heads()) == 1
    assert len(list(script.walk_revisions())) == 1


def test_sixteen_settings_seeded_with_unset_freshness(migrated_url: str) -> None:
    engine = create_engine(migrated_url)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT setting_key, value_text, approval_status FROM app_settings")
        ).all()
    engine.dispose()
    assert len(rows) == 16
    freshness = [r for r in rows if r[0].startswith("freshness.max_age_seconds.")]
    assert len(freshness) == 4
    assert all(r[1] is None and r[2] == "not_set" for r in freshness)
    by_key = {r[0]: r for r in rows}
    assert by_key["auth.login_max_failures"][1] == "5"
    assert by_key["session.inactivity_timeout_minutes"][1] == "15"


def test_downgrade_then_upgrade(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'd.db').as_posix()}"
    config = Config(str(_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")


def test_factories_build_every_table(db_session: Session) -> None:
    customer = factories.make_customer(db_session)
    user = factories.make_user(db_session, customer=customer, persona="customer01")
    factories.make_session(db_session, user)
    admin = factories.make_user(db_session, persona="admin01")
    account = factories.make_account(db_session, customer)
    card = factories.make_card(db_session, account)
    breakdown = factories.make_breakdown(db_session, account)
    factories.make_category(db_session, breakdown)
    txn = factories.make_transaction(db_session, account, card_id=card.id)
    pay = factories.make_payment(db_session, account)
    factories.make_tracking_event(db_session, account)
    factories.make_tracking_event(
        db_session, account, tracked_entity_type="transaction", tracked_entity_id=txn.id, transaction_id=txn.id
    )
    factories.make_tracking_event(
        db_session, account, tracked_entity_type="payment", tracked_entity_id=pay.id, payment_id=pay.id
    )
    factories.make_audit_entry(db_session, actor_user_id=admin.id)
    factories.make_data_rights_request(db_session, subject_customer_id=customer.id, requested_by_user_id=user.id)
    db_session.commit()
    assert db_session.get(type(account), account.id).customer_id == customer.id


def test_timestamps_round_trip_as_utc(db_session: Session) -> None:
    from app.utils import to_utc

    account = factories.make_account(db_session, factories.make_customer(db_session))
    txn = factories.make_transaction(db_session, account)
    db_session.commit()
    db_session.expire_all()
    stored = db_session.get(type(txn), txn.id)
    assert stored is not None
    assert to_utc(stored.transaction_time) == factories.NOW


def test_constraints_enforced(db_session: Session) -> None:
    customer = factories.make_customer(db_session)
    account = factories.make_account(db_session, customer)
    bad_builders = [
        lambda: factories.make_card(db_session, account, masked_pan="1234567890"),
        lambda: factories.make_payment(db_session, account, source_masked_account="12345678"),
        lambda: factories.make_user(db_session, persona="admin01", password_hash="x" * 60),
        lambda: factories.make_session(
            db_session, factories.make_user(db_session, customer=customer), revoked_at=factories.NOW
        ),
        lambda: factories.make_audit_entry(db_session, correlation_id=""),
    ]
    for build in bad_builders:
        with pytest.raises(IntegrityError):
            with db_session.begin_nested():
                build()


def test_card_must_belong_to_same_account(db_session: Session) -> None:
    customer = factories.make_customer(db_session)
    first = factories.make_account(db_session, customer)
    second = factories.make_account(db_session, customer)
    card = factories.make_card(db_session, first)
    db_session.commit()
    with pytest.raises(IntegrityError):
        factories.make_transaction(db_session, second, card_id=card.id)


def test_mask_check_and_adapters() -> None:
    from app.adapters import AccountSourceAdapter
    from app.utils import mask_check

    assert mask_check("**** 4821") == "**** 4821"
    assert mask_check(None) is None
    with pytest.raises(MaskingViolationError):
        mask_check("4111111111111111")
    with pytest.raises(AdapterNotEnabledError):
        AccountSourceAdapter().fetch("ACC-1")


def test_settings_rules() -> None:
    from app.config import Settings

    secret = "x" * 40
    for env in ("development", "local"):
        assert Settings(environment=env, jwt_secret_key=secret).is_non_deployed
    with pytest.raises(ValueError):
        Settings(environment="production", jwt_secret_key="short")
    with pytest.raises(ValueError):
        Settings(environment="development", jwt_secret_key=secret, cors_origins="*")
    assert not Settings(environment="production", jwt_secret_key=secret).is_non_deployed
    assert os.environ["ENVIRONMENT"] == "test"

"""Baseline schema: 13 tables, indexes and the 16 seeded app_settings keys.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-01-01 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

TS = sa.DateTime(timezone=True)
NOW = sa.text("CURRENT_TIMESTAMP")
MONEY = sa.Numeric(14, 2)
RATE = sa.Numeric(7, 3)


def _pk(table: str) -> sa.PrimaryKeyConstraint:
    return sa.PrimaryKeyConstraint("id", name=f"pk_{table}")


def _ts_pair() -> list[sa.Column]:  # type: ignore[type-arg]
    return [
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    ]


def _id() -> sa.Column:  # type: ignore[type-arg]
    return sa.Column("id", sa.Uuid(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "customers",
        _id(),
        sa.Column("source_ref", sa.String(40)),
        sa.Column("customer_since", sa.Date()),
        sa.Column("marketing_consent", sa.Boolean()),
        *_ts_pair(),
        _pk("customers"),
        sa.UniqueConstraint("source_ref", name="uq_customers_source_ref"),
    )

    op.create_table(
        "app_users",
        _id(),
        sa.Column("customer_id", sa.Uuid()),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("last_login_at", TS),
        *_ts_pair(),
        _pk("app_users"),
        sa.UniqueConstraint("username", name="uq_app_users_username"),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"], name="fk_app_users_customer", ondelete="CASCADE"
        ),
        sa.CheckConstraint("role IN ('customer', 'administrator')", name="ck_app_users_role"),
        sa.CheckConstraint("role <> 'customer' OR customer_id IS NOT NULL", name="ck_app_users_customer_link"),
        sa.CheckConstraint(
            "length(password_hash) = 60 AND substr(password_hash, 1, 2) = '$2' "
            "AND substr(password_hash, 5, 2) >= '12'",
            name="ck_app_users_bcrypt",
        ),
    )

    op.create_table(
        "user_sessions",
        _id(),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("issued_at", TS, nullable=False),
        sa.Column("expires_at", TS, nullable=False),
        sa.Column("last_activity_at", TS, nullable=False),
        sa.Column("revoked_at", TS),
        sa.Column("revocation_reason", sa.String(20)),
        *_ts_pair(),
        _pk("user_sessions"),
        sa.UniqueConstraint("token_hash", name="uq_user_sessions_token_hash"),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], name="fk_user_sessions_user", ondelete="CASCADE"),
        sa.CheckConstraint("length(token_hash) = 64", name="ck_user_sessions_hash_len"),
        sa.CheckConstraint("expires_at > issued_at", name="ck_user_sessions_expiry"),
        sa.CheckConstraint("last_activity_at >= issued_at", name="ck_user_sessions_activity"),
        sa.CheckConstraint(
            "revocation_reason IS NULL OR revocation_reason IN ('logout', 'inactivity', 'administrative')",
            name="ck_user_sessions_reason",
        ),
        sa.CheckConstraint(
            "(revoked_at IS NULL AND revocation_reason IS NULL) "
            "OR (revoked_at IS NOT NULL AND revocation_reason IS NOT NULL)",
            name="ck_user_sessions_revoked_pair",
        ),
    )

    op.create_table(
        "accounts",
        _id(),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("source_ref", sa.String(40)),
        sa.Column("product_name", sa.String(100), nullable=False),
        sa.Column("account_status", sa.String(40), nullable=False),
        sa.Column("opened_on", sa.Date()),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("credit_limit", MONEY),
        sa.Column("available_credit", MONEY),
        sa.Column("current_balance", MONEY),
        sa.Column("standard_purchase_apr", RATE),
        sa.Column("last_statement_balance", MONEY),
        sa.Column("next_statement_date", sa.Date()),
        sa.Column("payment_due_date", sa.Date()),
        sa.Column("minimum_payment", MONEY),
        *_ts_pair(),
        _pk("accounts"),
        sa.UniqueConstraint("source_ref", name="uq_accounts_source_ref"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], name="fk_accounts_customer", ondelete="CASCADE"),
        sa.CheckConstraint("length(account_status) > 0", name="ck_accounts_status_nonblank"),
        sa.CheckConstraint("length(currency) = 3", name="ck_accounts_currency"),
        sa.CheckConstraint("credit_limit IS NULL OR credit_limit >= 0", name="ck_accounts_credit_limit"),
        sa.CheckConstraint("available_credit IS NULL OR available_credit >= 0", name="ck_accounts_available_credit"),
        sa.CheckConstraint(
            "standard_purchase_apr IS NULL OR (standard_purchase_apr >= 0 AND standard_purchase_apr <= 100)",
            name="ck_accounts_apr",
        ),
        sa.CheckConstraint("minimum_payment IS NULL OR minimum_payment >= 0", name="ck_accounts_min_payment"),
    )

    op.create_table(
        "cards",
        _id(),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("source_ref", sa.String(40)),
        sa.Column("masked_pan", sa.String(12), nullable=False),
        sa.Column("card_status", sa.String(30), nullable=False),
        sa.Column("expiry_month_year", sa.String(7)),
        sa.Column("is_digital", sa.Boolean()),
        *_ts_pair(),
        _pk("cards"),
        sa.UniqueConstraint("source_ref", name="uq_cards_source_ref"),
        sa.UniqueConstraint("id", "account_id", name="uq_cards_id_account"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_cards_account", ondelete="CASCADE"),
        sa.CheckConstraint("masked_pan LIKE '****%'", name="ck_cards_masked"),
        sa.CheckConstraint("card_status IN ('Active', 'PendingActivation')", name="ck_cards_status"),
        sa.CheckConstraint("expiry_month_year IS NULL OR length(expiry_month_year) = 7", name="ck_cards_expiry"),
    )

    op.create_table(
        "balance_breakdowns",
        _id(),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("source_ref", sa.String(40)),
        sa.Column("as_of", TS),
        sa.Column("total_outstanding", MONEY),
        sa.Column("pending_total", MONEY),
        sa.Column("is_zero_balance", sa.Boolean()),
        sa.Column("purchases_subtotal", MONEY),
        sa.Column("balance_transfers_subtotal", MONEY),
        *_ts_pair(),
        _pk("balance_breakdowns"),
        sa.UniqueConstraint("source_ref", name="uq_balance_breakdowns_source_ref"),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name="fk_balance_breakdowns_account", ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "total_outstanding IS NULL OR total_outstanding >= 0", name="ck_balance_breakdowns_outstanding"
        ),
        sa.CheckConstraint("pending_total IS NULL OR pending_total >= 0", name="ck_balance_breakdowns_pending"),
        sa.CheckConstraint(
            "purchases_subtotal IS NULL OR purchases_subtotal >= 0", name="ck_balance_breakdowns_purchases"
        ),
        sa.CheckConstraint(
            "balance_transfers_subtotal IS NULL OR balance_transfers_subtotal >= 0",
            name="ck_balance_breakdowns_bt",
        ),
    )

    op.create_table(
        "balance_categories",
        _id(),
        sa.Column("breakdown_id", sa.Uuid(), nullable=False),
        sa.Column("source_ref", sa.String(40)),
        sa.Column("category_type", sa.String(30), nullable=False),
        sa.Column("category_label", sa.String(100), nullable=False),
        sa.Column("display_rank", sa.Integer(), nullable=False),
        sa.Column("category_balance", MONEY),
        sa.Column("category_apr_percent", RATE),
        sa.Column("promo_end_date", sa.Date()),
        sa.Column("revert_rate_percent", RATE),
        sa.Column("days_to_expiry", sa.Integer()),
        sa.Column("source_balance_transfer_ref", sa.String(40)),
        sa.Column("source_instalment_plan_ref", sa.String(40)),
        *_ts_pair(),
        _pk("balance_categories"),
        sa.UniqueConstraint("source_ref", name="uq_balance_categories_source_ref"),
        sa.UniqueConstraint("breakdown_id", "display_rank", name="uq_balance_categories_rank"),
        sa.ForeignKeyConstraint(
            ["breakdown_id"],
            ["balance_breakdowns.id"],
            name="fk_balance_categories_breakdown",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "category_type IN ('StandardPurchase', 'PromotionalPurchase', 'BalanceTransfer', 'Instalment')",
            name="ck_balance_categories_type",
        ),
        sa.CheckConstraint("display_rank >= 1", name="ck_balance_categories_rank"),
        sa.CheckConstraint("category_balance IS NULL OR category_balance >= 0", name="ck_balance_categories_balance"),
        sa.CheckConstraint(
            "category_apr_percent IS NULL OR (category_apr_percent >= 0 AND category_apr_percent <= 100)",
            name="ck_balance_categories_apr",
        ),
        sa.CheckConstraint(
            "revert_rate_percent IS NULL OR (revert_rate_percent >= 0 AND revert_rate_percent <= 100)",
            name="ck_balance_categories_revert",
        ),
        sa.CheckConstraint("days_to_expiry IS NULL OR days_to_expiry >= 0", name="ck_balance_categories_days"),
    )

    op.create_table(
        "transactions",
        _id(),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid()),
        sa.Column("source_ref", sa.String(40)),
        sa.Column("transaction_status", sa.String(30), nullable=False),
        sa.Column("transaction_time", TS, nullable=False),
        sa.Column("posted_date", sa.Date()),
        sa.Column("transaction_amount", MONEY, nullable=False),
        sa.Column("merchant_name", sa.String(100)),
        sa.Column("merchant_category_code", sa.String(4)),
        sa.Column("eligible_for_instalment", sa.Boolean()),
        *_ts_pair(),
        _pk("transactions"),
        sa.UniqueConstraint("source_ref", name="uq_transactions_source_ref"),
        sa.UniqueConstraint("id", "account_id", name="uq_transactions_id_account"),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name="fk_transactions_account", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["card_id", "account_id"],
            ["cards.id", "cards.account_id"],
            name="fk_transactions_card_account",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("transaction_status IN ('Pending', 'Posted')", name="ck_transactions_status"),
        sa.CheckConstraint(
            "merchant_category_code IS NULL OR length(merchant_category_code) = 4", name="ck_transactions_mcc"
        ),
    )

    op.create_table(
        "payments",
        _id(),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("source_ref", sa.String(40)),
        sa.Column("via_mandate_ref", sa.String(40)),
        sa.Column("payment_type", sa.String(30), nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=False),
        sa.Column("payment_status", sa.String(30), nullable=False),
        sa.Column("payment_amount", MONEY, nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("source_bank_name", sa.String(100)),
        sa.Column("source_masked_account", sa.String(12)),
        *_ts_pair(),
        _pk("payments"),
        sa.UniqueConstraint("source_ref", name="uq_payments_source_ref"),
        sa.UniqueConstraint("id", "account_id", name="uq_payments_id_account"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_payments_account", ondelete="CASCADE"),
        sa.CheckConstraint(
            "payment_type IN ('OneOff', 'Scheduled', 'DirectDebitCollection')", name="ck_payments_type"
        ),
        sa.CheckConstraint(
            "payment_method IN ('FasterPayments', 'DebitCard', 'DirectDebit')", name="ck_payments_method"
        ),
        sa.CheckConstraint(
            "payment_status IN ('Completed', 'Processing', 'Failed', 'Submitted', 'Cancelled')",
            name="ck_payments_status",
        ),
        sa.CheckConstraint("payment_amount >= 0", name="ck_payments_amount"),
        sa.CheckConstraint(
            "source_masked_account IS NULL OR source_masked_account LIKE '****%'", name="ck_payments_masked"
        ),
    )

    op.create_table(
        "tracking_events",
        _id(),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid()),
        sa.Column("payment_id", sa.Uuid()),
        sa.Column("tracked_entity_type", sa.String(20), nullable=False),
        sa.Column("tracked_entity_id", sa.Uuid(), nullable=False),
        sa.Column("lifecycle_status", sa.String(40), nullable=False),
        sa.Column("source_time", TS),
        sa.Column("provenance", sa.String(100), nullable=False),
        sa.Column("occurred_at", TS, nullable=False, server_default=NOW),
        _pk("tracking_events"),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name="fk_tracking_events_account", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id", "account_id"],
            ["transactions.id", "transactions.account_id"],
            name="fk_tracking_events_transaction",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id", "account_id"],
            ["payments.id", "payments.account_id"],
            name="fk_tracking_events_payment",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "tracked_entity_type IN ('account', 'transaction', 'payment')", name="ck_tracking_events_type"
        ),
        sa.CheckConstraint("length(lifecycle_status) > 0", name="ck_tracking_events_status_nonblank"),
        sa.CheckConstraint(
            "(tracked_entity_type = 'account' AND transaction_id IS NULL AND payment_id IS NULL "
            "AND tracked_entity_id = account_id) "
            "OR (tracked_entity_type = 'transaction' AND transaction_id IS NOT NULL AND payment_id IS NULL "
            "AND tracked_entity_id = transaction_id) "
            "OR (tracked_entity_type = 'payment' AND payment_id IS NOT NULL AND transaction_id IS NULL "
            "AND tracked_entity_id = payment_id)",
            name="ck_tracking_events_target",
        ),
    )

    op.create_table(
        "audit_log",
        _id(),
        sa.Column("occurred_at", TS, nullable=False, server_default=NOW),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", sa.String(64)),
        sa.Column("actor_user_id", sa.Uuid()),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("detail", sa.String(500)),
        _pk("audit_log"),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["app_users.id"], name="fk_audit_log_actor", ondelete="SET NULL"
        ),
        sa.CheckConstraint("severity IN ('info', 'warning', 'error', 'critical')", name="ck_audit_log_severity"),
        sa.CheckConstraint(
            "event_type IN ('login_success', 'login_failure', 'logout', 'data_rights_request_created', "
            "'data_rights_export', 'data_rights_deletion', 'admin_action')",
            name="ck_audit_log_event_type",
        ),
        sa.CheckConstraint("length(correlation_id) > 0", name="ck_audit_log_correlation_nonblank"),
    )

    op.create_table(
        "data_rights_requests",
        _id(),
        sa.Column("subject_customer_id", sa.Uuid()),
        sa.Column("subject_ref", sa.String(40), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid()),
        sa.Column("request_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'received'")),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("requested_at", TS, nullable=False, server_default=NOW),
        sa.Column("due_at", TS, nullable=False),
        sa.Column("completed_at", TS),
        sa.Column("outcome_summary", sa.String(500)),
        *_ts_pair(),
        _pk("data_rights_requests"),
        sa.UniqueConstraint("requested_by_user_id", "idempotency_key", name="uq_data_rights_idempotency"),
        sa.ForeignKeyConstraint(
            ["subject_customer_id"], ["customers.id"], name="fk_data_rights_subject", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"], ["app_users.id"], name="fk_data_rights_requester", ondelete="SET NULL"
        ),
        sa.CheckConstraint("request_type IN ('export', 'deletion')", name="ck_data_rights_type"),
        sa.CheckConstraint(
            "status IN ('received', 'in_progress', 'fulfilled', 'declined')", name="ck_data_rights_status"
        ),
        sa.CheckConstraint("due_at > requested_at", name="ck_data_rights_due"),
        sa.CheckConstraint(
            "(status IN ('fulfilled', 'declined') AND completed_at IS NOT NULL) "
            "OR (status IN ('received', 'in_progress') AND completed_at IS NULL)",
            name="ck_data_rights_completion",
        ),
        sa.CheckConstraint("length(idempotency_key) > 0", name="ck_data_rights_key_nonblank"),
    )

    app_settings = op.create_table(
        "app_settings",
        _id(),
        sa.Column("setting_key", sa.String(100), nullable=False),
        sa.Column("value_text", sa.String(200)),
        sa.Column("value_type", sa.String(10), nullable=False),
        sa.Column("approval_status", sa.String(25), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        *_ts_pair(),
        _pk("app_settings"),
        sa.UniqueConstraint("setting_key", name="uq_app_settings_key"),
        sa.CheckConstraint("value_type IN ('integer', 'decimal', 'text')", name="ck_app_settings_type"),
        sa.CheckConstraint(
            "approval_status IN ('approved', 'approval_pending', 'not_set', 'prototype_default', "
            "'requirement_baseline')",
            name="ck_app_settings_approval",
        ),
        sa.CheckConstraint(
            "(value_text IS NULL AND approval_status = 'not_set') "
            "OR (value_text IS NOT NULL AND approval_status <> 'not_set')",
            name="ck_app_settings_value",
        ),
    )

    indexes: list[tuple[str, str, list[str]]] = [
        ("ix_app_users_customer_id", "app_users", ["customer_id"]),
        ("ix_user_sessions_user_id", "user_sessions", ["user_id"]),
        ("ix_user_sessions_expires_at", "user_sessions", ["expires_at"]),
        ("ix_user_sessions_last_activity", "user_sessions", ["last_activity_at"]),
        ("ix_accounts_customer_id", "accounts", ["customer_id"]),
        ("ix_cards_account_id", "cards", ["account_id"]),
        ("ix_balance_breakdowns_account_asof", "balance_breakdowns", ["account_id", "as_of"]),
        ("ix_transactions_account_time", "transactions", ["account_id", "transaction_time"]),
        ("ix_transactions_card_id", "transactions", ["card_id"]),
        ("ix_payments_account_date", "payments", ["account_id", "payment_date"]),
        ("ix_tracking_events_account_occurred", "tracking_events", ["account_id", "occurred_at"]),
        ("ix_tracking_events_transaction_id", "tracking_events", ["transaction_id"]),
        ("ix_tracking_events_payment_id", "tracking_events", ["payment_id"]),
        ("ix_audit_log_occurred_at", "audit_log", ["occurred_at"]),
        ("ix_audit_log_correlation_id", "audit_log", ["correlation_id"]),
        ("ix_audit_log_actor_user_id", "audit_log", ["actor_user_id"]),
        ("ix_audit_log_event_occurred", "audit_log", ["event_type", "occurred_at"]),
        ("ix_data_rights_subject_customer", "data_rights_requests", ["subject_customer_id"]),
        ("ix_data_rights_requester", "data_rights_requests", ["requested_by_user_id"]),
        ("ix_data_rights_status_due", "data_rights_requests", ["status", "due_at"]),
    ]
    for name, table, columns in indexes:
        op.create_index(name, table, columns)

    def _setting(n: int, key: str, value: str | None, vtype: str, status: str, desc: str) -> dict[str, object]:
        import uuid

        return {
            "id": uuid.UUID(f"00000000-0000-4000-8000-{n:012d}"),
            "setting_key": key,
            "value_text": value,
            "value_type": vtype,
            "approval_status": status,
            "description": desc,
        }

    op.bulk_insert(
        app_settings,
        [
            _setting(1, "freshness.max_age_seconds.balance_breakdown", None, "integer", "not_set",
                     "Approved maximum age of a balance breakdown as_of; unset until the data and integration owner approves one (NFR-039)."),
            _setting(2, "freshness.max_age_seconds.transaction", None, "integer", "not_set",
                     "Approved maximum age for transaction source time; unset until approved (NFR-039)."),
            _setting(3, "freshness.max_age_seconds.payment", None, "integer", "not_set",
                     "Approved maximum age for payment source date; unset until approved (NFR-039)."),
            _setting(4, "freshness.max_age_seconds.tracking_event", None, "integer", "not_set",
                     "Approved maximum age for tracking event source time; unset until approved (NFR-039)."),
            _setting(5, "audit.retention_months", "12", "integer", "approval_pending",
                     "Proposed audit retention; approval-gated, not an approved enterprise policy (NFR-019)."),
            _setting(6, "data_rights.fulfilment_days", "30", "integer", "requirement_baseline",
                     "Calendar days to fulfil a data-rights request (NFR-016); drives data_rights_requests.due_at."),
            _setting(7, "demo.data_retention_days_after_period", "30", "integer", "requirement_baseline",
                     "Calendar days after the demonstration period when synthetic data is deleted unless an extension is approved (NFR-036)."),
            _setting(8, "session.inactivity_timeout_minutes", "15", "integer", "prototype_default",
                     "Server-enforced inactivity timeout; prototype default, not an approved policy value (NFR-009)."),
            _setting(9, "session.max_lifetime_minutes", "60", "integer", "prototype_default",
                     "Session expiry window used to set user_sessions.expires_at; prototype default (NFR-009)."),
            _setting(10, "session.logout_invalidation_seconds", "60", "integer", "requirement_baseline",
                     "A logged-out token is rejected within this many seconds (NFR-009)."),
            _setting(11, "auth.login_max_failures", "5", "integer", "requirement_baseline",
                     "Failed logins per source IP before HTTP 429 (NFR-010); the counter is in-process for the single-instance prototype."),
            _setting(12, "auth.login_window_minutes", "15", "integer", "requirement_baseline",
                     "Rolling window for the login failure limit (NFR-010)."),
            _setting(13, "pagination.default_limit", "25", "integer", "prototype_default",
                     "Default page size for transactions, payments and tracking events."),
            _setting(14, "pagination.max_limit", "100", "integer", "prototype_default",
                     "Maximum page size for unbounded lists."),
            _setting(15, "availability.demonstration_target_percent", "99.0", "decimal", "approval_pending",
                     "Assumption: demonstration availability target; approval-gated (NFR-005)."),
            _setting(16, "accessibility.baseline", "WCAG 2.2 AA", "text", "approval_pending",
                     "Assumption: accessibility baseline; no conformance claim before stakeholder approval (NFR-021)."),
        ],
    )


def downgrade() -> None:
    for table in (
        "app_settings",
        "data_rights_requests",
        "audit_log",
        "tracking_events",
        "payments",
        "transactions",
        "balance_categories",
        "balance_breakdowns",
        "cards",
        "accounts",
        "user_sessions",
        "app_users",
        "customers",
    ):
        op.drop_table(table)

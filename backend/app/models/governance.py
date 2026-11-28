"""Audit log, data-rights requests and policy settings."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._columns import UTC_DATETIME, created_at_column, updated_at_column, utcnow, uuid_pk


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_audit_log"),
        CheckConstraint("severity IN ('info', 'warning', 'error', 'critical')", name="ck_audit_log_severity"),
        CheckConstraint(
            "event_type IN ('login_success', 'login_failure', 'logout', 'data_rights_request_created', "
            "'data_rights_export', 'data_rights_deletion', 'admin_action')",
            name="ck_audit_log_event_type",
        ),
        CheckConstraint("length(correlation_id) > 0", name="ck_audit_log_correlation_nonblank"),
        Index("ix_audit_log_occurred_at", "occurred_at"),
        Index("ix_audit_log_correlation_id", "correlation_id"),
        Index("ix_audit_log_actor_user_id", "actor_user_id"),
        Index("ix_audit_log_event_occurred", "event_type", "occurred_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    occurred_at: Mapped[datetime] = mapped_column(
        UTC_DATETIME, nullable=False, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64))
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("app_users.id", name="fk_audit_log_actor", ondelete="SET NULL")
    )
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[str | None] = mapped_column(String(500))


class DataRightsRequest(Base):
    __tablename__ = "data_rights_requests"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_data_rights_requests"),
        UniqueConstraint("requested_by_user_id", "idempotency_key", name="uq_data_rights_idempotency"),
        CheckConstraint("request_type IN ('export', 'deletion')", name="ck_data_rights_type"),
        CheckConstraint(
            "status IN ('received', 'in_progress', 'fulfilled', 'declined')", name="ck_data_rights_status"
        ),
        CheckConstraint("due_at > requested_at", name="ck_data_rights_due"),
        CheckConstraint(
            "(status IN ('fulfilled', 'declined') AND completed_at IS NOT NULL) "
            "OR (status IN ('received', 'in_progress') AND completed_at IS NULL)",
            name="ck_data_rights_completion",
        ),
        CheckConstraint("length(idempotency_key) > 0", name="ck_data_rights_key_nonblank"),
        Index("ix_data_rights_subject_customer", "subject_customer_id"),
        Index("ix_data_rights_requester", "requested_by_user_id"),
        Index("ix_data_rights_status_due", "status", "due_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    subject_customer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("customers.id", name="fk_data_rights_subject", ondelete="SET NULL")
    )
    subject_ref: Mapped[str] = mapped_column(String(40), nullable=False)
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("app_users.id", name="fk_data_rights_requester", ondelete="SET NULL")
    )
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="received", server_default=text("'received'")
    )
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        UTC_DATETIME, nullable=False, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )
    due_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME)
    outcome_summary: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class AppSetting(Base):
    __tablename__ = "app_settings"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_settings"),
        UniqueConstraint("setting_key", name="uq_app_settings_key"),
        CheckConstraint("value_type IN ('integer', 'decimal', 'text')", name="ck_app_settings_type"),
        CheckConstraint(
            "approval_status IN ('approved', 'approval_pending', 'not_set', 'prototype_default', "
            "'requirement_baseline')",
            name="ck_app_settings_approval",
        ),
        CheckConstraint(
            "(value_text IS NULL AND approval_status = 'not_set') "
            "OR (value_text IS NOT NULL AND approval_status <> 'not_set')",
            name="ck_app_settings_value",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    setting_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_text: Mapped[str | None] = mapped_column(String(200))
    value_type: Mapped[str] = mapped_column(String(10), nullable=False)
    approval_status: Mapped[str] = mapped_column(String(25), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

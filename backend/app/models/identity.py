"""Identity and ownership tables: customers, app_users, user_sessions."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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
from app.models._columns import UTC_DATETIME, created_at_column, updated_at_column, uuid_pk


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_customers"),
        UniqueConstraint("source_ref", name="uq_customers_source_ref"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    source_ref: Mapped[str | None] = mapped_column(String(40))
    customer_since: Mapped[date | None] = mapped_column(Date)
    marketing_consent: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class AppUser(Base):
    __tablename__ = "app_users"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_users"),
        UniqueConstraint("username", name="uq_app_users_username"),
        CheckConstraint("role IN ('customer', 'administrator')", name="ck_app_users_role"),
        CheckConstraint("role <> 'customer' OR customer_id IS NOT NULL", name="ck_app_users_customer_link"),
        CheckConstraint(
            "length(password_hash) = 60 AND substr(password_hash, 1, 2) = '$2' "
            "AND substr(password_hash, 5, 2) >= '12'",
            name="ck_app_users_bcrypt",
        ),
        Index("ix_app_users_customer_id", "customer_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("customers.id", name="fk_app_users_customer", ondelete="CASCADE")
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("TRUE")
    )
    last_login_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_user_sessions"),
        UniqueConstraint("token_hash", name="uq_user_sessions_token_hash"),
        CheckConstraint("length(token_hash) = 64", name="ck_user_sessions_hash_len"),
        CheckConstraint("expires_at > issued_at", name="ck_user_sessions_expiry"),
        CheckConstraint("last_activity_at >= issued_at", name="ck_user_sessions_activity"),
        CheckConstraint(
            "revocation_reason IS NULL OR revocation_reason IN ('logout', 'inactivity', 'administrative')",
            name="ck_user_sessions_reason",
        ),
        CheckConstraint(
            "(revoked_at IS NULL AND revocation_reason IS NULL) "
            "OR (revoked_at IS NOT NULL AND revocation_reason IS NOT NULL)",
            name="ck_user_sessions_revoked_pair",
        ),
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_expires_at", "expires_at"),
        Index("ix_user_sessions_last_activity", "last_activity_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("app_users.id", name="fk_user_sessions_user", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME)
    revocation_reason: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

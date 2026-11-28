"""Parameterized access to `app_users`."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AppUser


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_username(self, username: str) -> AppUser | None:
        return self.db.scalar(select(AppUser).where(AppUser.username == username))

    def get_by_id(self, user_id: uuid.UUID) -> AppUser | None:
        return self.db.get(AppUser, user_id)

    def touch_last_login(self, user: AppUser, when: datetime) -> None:
        user.last_login_at = when
        self.db.flush()

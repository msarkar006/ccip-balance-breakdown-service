"""Read-only access to `app_settings` values."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AppSetting


class SettingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_int(self, key: str, default: int) -> int:
        value = self.db.scalar(select(AppSetting.value_text).where(AppSetting.setting_key == key))
        try:
            return int(value) if value is not None else default
        except ValueError:
            return default

    def get_many(self, keys: list[str]) -> dict[str, str | None]:
        """Return `value_text` for each requested key (None when unset or absent)."""
        rows = self.db.execute(
            select(AppSetting.setting_key, AppSetting.value_text).where(AppSetting.setting_key.in_(keys))
        ).all()
        found = {k: v for k, v in rows}
        return {key: found.get(key) for key in keys}


SettingsRepository = SettingRepository

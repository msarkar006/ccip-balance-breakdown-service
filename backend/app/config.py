"""Typed environment settings. Validated when the app is created, not on first use."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

NON_DEPLOYED_ENVIRONMENTS = frozenset({"development", "local", "test"})
MIN_SECRET_LENGTH = 32


class SettingsError(ValueError):
    """Raised at startup when configuration is unsafe or incomplete."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./app.db"
    jwt_secret_key: str = ""
    cors_origins: str = "http://localhost:5173"
    debug: bool = False
    seed_enabled: bool = False
    environment: str = "production"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    otel_exporter_endpoint: str = ""

    @field_validator("environment")
    @classmethod
    def _normalise_environment(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_level(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value

    @property
    def is_non_deployed(self) -> bool:
        """`development` and `local` (and `test`) are the non-deployed modes."""
        return self.environment in NON_DEPLOYED_ENVIRONMENTS

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def docs_enabled(self) -> bool:
        return self.debug or self.is_non_deployed

    @model_validator(mode="after")
    def _check_deployment_safety(self) -> Settings:
        if "*" in self.cors_origin_list:
            raise SettingsError("CORS_ORIGINS must be an explicit allow-list; '*' is not permitted")
        if not self.is_non_deployed:
            if len(self.jwt_secret_key) < MIN_SECRET_LENGTH or self.jwt_secret_key.startswith(
                ("replace-with", "dev-only")
            ):
                raise SettingsError(
                    "JWT_SECRET_KEY must be set to a generated secret of at least 32 characters "
                    "when ENVIRONMENT is not development/local. Generate one with: "
                    'python -c "import secrets;print(secrets.token_urlsafe(48))"'
                )
        elif len(self.jwt_secret_key) < MIN_SECRET_LENGTH:
            raise SettingsError(
                "JWT_SECRET_KEY is empty or shorter than 32 characters; copy backend/dev.env to backend/.env"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

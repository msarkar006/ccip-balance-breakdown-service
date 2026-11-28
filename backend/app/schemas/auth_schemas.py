"""Auth request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common_schemas import ApiModel


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128, repr=False)


class UserSummary(ApiModel):
    id: uuid.UUID
    username: str
    role: Literal["customer", "administrator"]
    customer_id: uuid.UUID | None


class LoginResponse(ApiModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"  # noqa: S105 - OAuth scheme name, not a secret
    issued_at: datetime
    expires_at: datetime
    inactivity_timeout_minutes: int
    user: UserSummary


class SessionInfo(ApiModel):
    user: UserSummary
    issued_at: datetime
    expires_at: datetime
    last_activity_at: datetime

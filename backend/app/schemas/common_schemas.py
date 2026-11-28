"""Shared response schemas: pagination envelope, page request and the Freshness label."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

T = TypeVar("T")

DEFAULT_LIMIT = 25
MAX_LIMIT = 100


class ApiModel(BaseModel):
    """Base for response models: camelCase on the wire, snake_case in code."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class Page(ApiModel, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class PageRequest(BaseModel):
    limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)
    offset: int = Field(default=0, ge=0)


FreshnessState = Literal["freshness unavailable", "unconfirmed freshness", "stale"]


class Freshness(ApiModel):
    state: FreshnessState
    basis: str = Field(max_length=200)
    source_time: datetime | None = None
    max_age_seconds: int | None = Field(default=None, ge=1)


class ErrorResponse(BaseModel):
    detail: str

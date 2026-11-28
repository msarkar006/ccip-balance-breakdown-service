"""Card response schemas: masked reference and source status only."""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BeforeValidator, Field

from app.schemas.common_schemas import ApiModel, Page
from app.utils import mask_check

MaskedPan = Annotated[str, BeforeValidator(mask_check), Field(max_length=12, pattern=r"^\*\*\*\*")]


class CardOut(ApiModel):
    id: uuid.UUID
    account_id: uuid.UUID
    source_ref: str | None = None
    masked_pan: MaskedPan
    card_status: str
    expiry_month_year: str | None = None
    is_digital: bool | None = None


CardPage = Page[CardOut]

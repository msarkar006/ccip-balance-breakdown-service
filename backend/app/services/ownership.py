"""OwnershipScope: the customer whose records a request may read."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends

from app.dependencies import CurrentUser, require_customer
from app.exceptions import ForbiddenError


@dataclass(frozen=True)
class OwnershipScope:
    customer_id: uuid.UUID


def get_ownership_scope(user: CurrentUser = Depends(require_customer)) -> OwnershipScope:
    if user.customer_id is None:
        raise ForbiddenError("customer role required")
    return OwnershipScope(customer_id=user.customer_id)

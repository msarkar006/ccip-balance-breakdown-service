"""InformationOnlyPolicy: the backend-enforced boundary against financial actions."""

from __future__ import annotations

import re

from app.exceptions import InformationOnlyViolationError

READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# The only non-read operations the prototype exposes: sign-in, sign-out and audited data-rights creation.
ALLOWED_WRITES: frozenset[tuple[str, str]] = frozenset(
    {
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/logout"),
        ("POST", "/api/v1/data-rights-requests"),
    }
)

PROHIBITED_VERBS = re.compile(
    r"(create|schedule|amend|cancel|redeem|enrol|enroll|convert|validate|select|complete|submit|pay|transfer)",
    re.IGNORECASE,
)


class InformationOnlyPolicy:
    ACCOUNT_NOTICE = (
        "Information only. Account details are shown as supplied and do not create or imply a servicing action."
    )
    PAYMENT_NOTICE = (
        "Information only. A payment status is a source record and is not proof of settlement or finality; "
        "no payment can be made, changed or cancelled here."
    )
    SNAPSHOT_NOTICE = (
        "Information only. This snapshot is shown as of its source time and is not current, real-time or final."
    )

    @staticmethod
    def assert_read_only(method: str, path: str) -> None:
        """Raise unless the request is a read or one of the three allowed writes."""
        method = method.upper()
        if method in READ_METHODS:
            return
        if (method, path.rstrip("/") or "/") in ALLOWED_WRITES:
            return
        raise InformationOnlyViolationError(f"blocked {method} request")

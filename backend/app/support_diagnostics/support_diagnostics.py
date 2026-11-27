"""
Support diagnostics router for diagnostic lookups and operational monitoring.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.middleware.auth import get_current_user
from app.models.app_user import AppUser
from app.support_diagnostics.support_diagnostics_schemas import (
    DiagnosticLookupRequest,
    DiagnosticLookupResponse,
    OperationalSummaryResponse,
)
from app.support_diagnostics.support_diagnostics_service import SupportDiagnosticsService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/support-diagnostics", tags=["support-diagnostics"])


def require_support_role(current_user: AppUser = Depends(get_current_user)) -> AppUser:
    """
    Require support role for support diagnostics endpoints.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if they have support role

    Raises:
        HTTPException: 403 if user is not support role
    """
    # In a full implementation, check user role against a roles table
    # For now, check if user email contains "support" as a simple indicator
    # In production, this would check AppUser.role or a separate role mapping

    # Support users should have a specific role field or flag
    # For this implementation, we'll check if the user's email starts with "support"
    if not current_user.email.startswith("support"):
        raise HTTPException(
            status_code=403,
            detail="Access denied. Support role required."
        )

    return current_user


@router.post("/lookups", response_model=DiagnosticLookupResponse)
def diagnostic_lookup(
    request: DiagnosticLookupRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_support_role)
) -> DiagnosticLookupResponse:
    """
    Perform diagnostic lookup for support investigations.

    Requires support role. Returns customer-visible state, lifecycle events,
    synchronization summary, and escalation context.

    Args:
        request: Diagnostic lookup request
        db: Database session
        current_user: Current authenticated support user

    Returns:
        DiagnosticLookupResponse with diagnostic information

    Raises:
        HTTPException: 403 if not support role, 404 if entity not found, 422 if validation fails
    """
    service = SupportDiagnosticsService(db)

    try:
        return service.lookup(
            request=request,
            support_user_id=current_user.id,
            correlation_id=None  # Would come from request context in production
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/operational-summary", response_model=OperationalSummaryResponse)
def operational_summary(
    window_minutes: int = Query(60, ge=5, le=1440, description="Time window in minutes"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_support_role)
) -> OperationalSummaryResponse:
    """
    Get operational summary with aggregated metrics.

    Requires support role. Returns metrics over the specified time window.
    No customer-identifying data is included.

    Args:
        window_minutes: Time window for aggregation (5-1440 minutes, default 60)
        db: Database session
        current_user: Current authenticated support user

    Returns:
        OperationalSummaryResponse with aggregated metrics

    Raises:
        HTTPException: 403 if not support role, 422 if validation fails
    """
    service = SupportDiagnosticsService(db)

    try:
        return service.operational_summary(window_minutes=window_minutes)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)


# Health endpoints router (unauthenticated)
health_router = APIRouter(prefix="/api/health", tags=["health"])


@health_router.get("/live")
def health_live():
    """
    Liveness probe - returns 200 when service process is running.

    No authentication required. No dependency checks.

    Returns:
        Status object with checked_at timestamp
    """
    return {
        "status": "ok",
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


@health_router.get("/ready")
def health_ready(db: Session = Depends(get_db)):
    """
    Readiness probe - returns 200 when service is ready to serve traffic.

    Checks database connectivity. Returns 503 if database is unavailable.
    No authentication required.

    Args:
        db: Database session

    Returns:
        Status object with checks array

    Raises:
        HTTPException: 503 if database is unavailable
    """
    checks = []

    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        checks.append({"component": "database", "status": "ok"})
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks.append({"component": "database", "status": "unavailable", "error": str(e)})
        raise HTTPException(
            status_code=503,
            detail={"status": "unavailable", "checks": checks}
        )

    return {
        "status": "ok",
        "checks": checks
    }

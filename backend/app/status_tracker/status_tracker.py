"""
Status tracker API router - unified lifecycle tracking endpoints.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.middleware.auth import get_current_user
from app.models.app_user import AppUser
from app.status_tracker.status_tracker_schemas import (
    TrackerListResponse,
    TrackerRefreshResponse,
)
from app.status_tracker.status_tracker_service import StatusTrackingService
from app.sync.sync_service import FreshnessAndSyncService

router = APIRouter(prefix="/api/v1/status-tracker", tags=["status-tracker"])

# Throttle tracking: entity_type/entity_id -> last_refresh_timestamp

_refresh_throttle: dict[str, datetime] = {}
_THROTTLE_WINDOW_SECONDS = 10


@router.get("", response_model=TrackerListResponse)
def get_tracker_list(
    account_id: int = Query(..., description="Account ID to retrieve tracker items for"),
    status_group: Optional[str] = Query(None, description="Status group filter: unresolved"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Get unified status tracker view.

    Aggregates TrackerItem from payments, money_transfers, balance_transfers,
    and direct_debit_change_requests.

    Filters:
    - account_id (required)
    - status_group=unresolved: only non-final states

    Returns:
    - Paginated tracker items ordered by last_updated_at DESC
    - unresolved_count: count of non-final items
    - overall_message: escalation guidance when all sources unavailable
    """
    service = StatusTrackingService(db)
    return service.get_tracker_view(
        account_id=account_id,
        status_group=status_group,
        limit=limit,
        offset=offset,
    )


@router.get("/{entity_type}/{entity_id}")
def get_tracker_detail(
    entity_type: str = Path(..., description="Entity type: Payment, MoneyTransfer, BalanceTransfer, DirectDebitChangeRequest"),
    entity_id: str = Path(..., description="Entity ID"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Get detailed tracker item with timeline.

    Returns:
    - TrackerItem with current state
    - milestones: Array of tracking events ordered by occurred_at ASC
    - timeline_freshness: Freshness of timeline data
    """
    service = StatusTrackingService(db)
    result = service.get_tracker_detail(
        entity_type=entity_type,
        entity_id=entity_id,
    )

    if not result:
        raise NotFoundError(f"{entity_type} {entity_id} not found")

    return result


@router.post("/{entity_type}/{entity_id}/refresh", response_model=TrackerRefreshResponse)
def refresh_tracker_item(
    entity_type: str = Path(..., description="Entity type: Payment, MoneyTransfer, BalanceTransfer, DirectDebitChangeRequest"),
    entity_id: str = Path(..., description="Entity ID"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Refresh tracker item by calling sync.

    Calls FreshnessAndSyncService.sync_one for the entity.
    Throttled to once per entity per 10 seconds.

    Returns:
    - tracker_item: Updated TrackerItem
    - refresh_outcome: "updated", "unchanged", or "failed"
    - refresh_message: Explanation of refresh result

    Raises:
    - 429 Too Many Requests if within throttle window
    """
    from datetime import datetime, timezone

    # Check throttle
    throttle_key = f"{entity_type}/{entity_id}"
    now = datetime.now(timezone.utc)

    if throttle_key in _refresh_throttle:
        last_refresh = _refresh_throttle[throttle_key]
        elapsed = (now - last_refresh).total_seconds()
        if elapsed < _THROTTLE_WINDOW_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Refresh throttled. Please wait {int(_THROTTLE_WINDOW_SECONDS - elapsed)} seconds before retrying.",
            )

    # Update throttle timestamp
    _refresh_throttle[throttle_key] = now

    # Call sync service
    sync_service = FreshnessAndSyncService()
    sync_outcome = sync_service.sync_one(entity_type=entity_type, entity_id=entity_id, db=db)

    # Get updated tracker item
    service = StatusTrackingService(db)
    result = service.get_tracker_detail(entity_type=entity_type, entity_id=entity_id)

    if not result:
        raise NotFoundError(f"{entity_type} {entity_id} not found")

    tracker_item = result["tracker_item"]

    # Map sync outcome to refresh outcome
    if sync_outcome == "success":
        refresh_outcome = "updated"
        refresh_message = "Status updated successfully from external source."
    elif sync_outcome == "no_change":
        refresh_outcome = "unchanged"
        refresh_message = "No new information available at this time."
    else:
        refresh_outcome = "failed"
        refresh_message = "Unable to refresh status at this time. The external source may be temporarily unavailable."

    return TrackerRefreshResponse(
        tracker_item=tracker_item,
        refresh_outcome=refresh_outcome,
        refresh_message=refresh_message,
    )

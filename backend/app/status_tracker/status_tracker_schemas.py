"""
Status tracker schemas - request/response models for status tracking.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class TrackerMilestone(BaseModel):
    """Single tracking event milestone."""

    event_timestamp: datetime
    milestone_label: str
    detail: Optional[str] = None


class TrackerEscalation(BaseModel):
    """Escalation guidance for unresolved items."""

    is_escalated: bool
    reason: Optional[str] = None
    guidance: Optional[str] = None


class TrackerGuidance(BaseModel):
    """Guidance message for tracker item."""

    message_code: str
    message: str
    next_step: Optional[str] = None


class TrackerFreshness(BaseModel):
    """Freshness information for tracker item."""

    level: Literal["Current", "Stale", "Unknown"]
    as_of: Optional[datetime] = None


class TrackerItem(BaseModel):
    """Unified tracker item for cross-entity tracking."""

    entity_type: str
    entity_id: str
    title: str
    lifecycle_state: str
    status_label: str
    is_final: bool
    amount: Optional[str] = None
    last_updated_at: datetime
    freshness: TrackerFreshness
    escalation: Optional[TrackerEscalation] = None
    guidance: Optional[TrackerGuidance] = None
    resource_path: str


class TrackerListResponse(BaseModel):
    """Paginated tracker list response."""

    items: list[TrackerItem]
    total: int
    limit: int
    offset: int
    has_more: bool
    unresolved_count: int
    overall_message: Optional[str] = None


class TrackerDetailResponse(BaseModel):
    """Detailed tracker item with timeline."""

    entity_type: str
    entity_id: str
    title: str
    lifecycle_state: str
    status_label: str
    is_final: bool
    amount: Optional[str] = None
    last_updated_at: datetime
    freshness: TrackerFreshness
    escalation: Optional[TrackerEscalation] = None
    guidance: Optional[TrackerGuidance] = None
    resource_path: str
    milestones: list[TrackerMilestone]
    timeline_freshness: TrackerFreshness


class RefreshOutcome(str):
    """Refresh outcome enum."""
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    FAILED = "failed"


class TrackerRefreshResponse(BaseModel):
    """Tracker refresh response."""

    tracker_item: TrackerItem
    refresh_outcome: str  # "updated", "unchanged", "failed"
    refresh_message: str

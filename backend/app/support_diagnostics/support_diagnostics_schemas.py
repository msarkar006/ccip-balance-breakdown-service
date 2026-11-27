"""
Support diagnostics schemas for diagnostic lookup and operational summary.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DiagnosticEvent(BaseModel):
    """Diagnostic event capturing lifecycle transitions."""
    event_timestamp: datetime
    event_type: str
    status: str
    source_system: Optional[str] = None
    source_event_reference: Optional[str] = None
    detail: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SynchronizationSummary(BaseModel):
    """Synchronization summary for an entity."""
    last_synchronized_at: Optional[datetime] = None
    sync_outcome: Optional[str] = None
    freshness_status: Optional[str] = None
    retry_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class RiskDecision(BaseModel):
    """Masked risk decision summary."""
    decision: str  # allow, review, restrict
    reason_code: Optional[str] = None
    # Detailed risk factors are masked for support view

    model_config = ConfigDict(from_attributes=True)


class EscalationContext(BaseModel):
    """Escalation context with recommended route."""
    recommended_route: str  # payment_operations, transfer_operations, fraud_and_risk_review, none
    traceable_references: List[str] = Field(default_factory=list)
    summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DiagnosticLookupRequest(BaseModel):
    """Request for diagnostic lookup."""
    verification_reference: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Verification reference for audit trail"
    )
    lookup_reason: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Reason for performing the lookup"
    )
    entity_type: Optional[str] = Field(
        None,
        description="Entity type (Payment, MoneyTransfer, BalanceTransfer, DirectDebitChangeRequest, Account)"
    )
    entity_id: Optional[str] = Field(
        None,
        description="Entity ID (required unless entity_type is Account)"
    )

    model_config = ConfigDict(from_attributes=True)


class DiagnosticLookupResponse(BaseModel):
    """Response for diagnostic lookup with customer-visible state."""
    lookup_id: str
    customer_visible_state: Dict[str, Any]
    lifecycle_events: List[DiagnosticEvent]
    synchronization_summary: SynchronizationSummary
    risk_decision: Optional[RiskDecision] = None
    escalation_context: EscalationContext

    model_config = ConfigDict(from_attributes=True)


class OperationalSummaryResponse(BaseModel):
    """Operational summary with aggregated metrics."""
    window_minutes: int
    auth_failure_rate: float  # percentage
    api_error_rate: float  # percentage
    api_latency_p95: float  # milliseconds
    stale_account_count: int
    invalid_synchronized_record_rate: float  # percentage
    top_failure_categories: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)

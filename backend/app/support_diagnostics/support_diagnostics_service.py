"""
Support diagnostics service for operational diagnostics and troubleshooting.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit.audit_service import AuditService
from app.models.audit_log import AuditLog
from app.core.errors import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.credit_card_account import CreditCardAccount
from app.models.synchronization_record import SynchronizationRecord
from app.models.tracking_event import TrackingEvent
from app.status_tracker.status_tracker_service import StatusTrackingService
from app.support_diagnostics.support_diagnostics_schemas import (
    DiagnosticEvent,
    DiagnosticLookupRequest,
    DiagnosticLookupResponse,
    EscalationContext,
    OperationalSummaryResponse,
    RiskDecision,
    SynchronizationSummary,
)

logger = get_logger(__name__)


class SupportDiagnosticsService:
    """Service for support diagnostics and operational monitoring."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
        self.status_tracker_service = StatusTrackingService(db)

    def lookup(
        self,
        request: DiagnosticLookupRequest,
        support_user_id: int,
        correlation_id: Optional[str] = None
    ) -> DiagnosticLookupResponse:
        """
        Perform diagnostic lookup for support investigations.

        Args:
            request: Diagnostic lookup request
            support_user_id: Support user ID performing the lookup
            correlation_id: Request correlation ID

        Returns:
            DiagnosticLookupResponse with customer-visible state

        Raises:
            ValidationError: If validation fails
            NotFoundError: If account or entity not found
        """
        # Validate entity_id requirement
        if request.entity_type and request.entity_type != "Account":
            if not request.entity_id:
                raise ValidationError(message="entity_id is required for non-Account entity types")

        # For Account entity type, we'll use account_id as the entity
        # For other types, we need to load the entity and get its account_id
        account_id = None

        if request.entity_type == "Account" or not request.entity_type:
            # Treat entity_id as account_id or derive from other entity
            if request.entity_id:
                account_id = int(request.entity_id)
            else:
                raise ValidationError(message="entity_id is required to identify the account")

            # Load account
            account = self.db.query(CreditCardAccount).filter(
                CreditCardAccount.id == account_id
            ).first()

            if not account:
                raise NotFoundError(message="Account not found")

            # Build customer-visible state from account
            customer_visible_state = {
                "entity_type": "Account",
                "entity_id": str(account.id),
                "account_number_masked": account.account_number_masked,
                "account_status": account.account_status,
                "current_balance": str(account.current_balance),
                "available_credit": str(account.available_credit),
            }

            # Get synchronization record for account
            sync_record = self.db.query(SynchronizationRecord).filter(
                SynchronizationRecord.entity_type == "Account",
                SynchronizationRecord.entity_id == str(account.id)
            ).order_by(SynchronizationRecord.last_sync_at.desc()).first()

            # Get tracking events for account-level events
            events = self.db.query(TrackingEvent).filter(
                TrackingEvent.entity_type == "Account",
                TrackingEvent.entity_id == str(account.id)
            ).order_by(TrackingEvent.occurred_at.asc()).all()

            risk_decision = None

        else:
            # Validate entity_id is present
            if not request.entity_id:
                raise ValidationError(message="entity_id is required for non-Account entity types")

            # Load entity through status tracker
            entity_detail = self.status_tracker_service.get_tracker_detail(
                entity_type=request.entity_type,
                entity_id=request.entity_id
            )

            if not entity_detail:
                raise NotFoundError(message=f"{request.entity_type} not found")

            tracker_item = entity_detail["tracker_item"]

            # Get account_id from entity directly
            from app.models.balance_transfer import BalanceTransfer
            from app.models.direct_debit_change_request import DirectDebitChangeRequest
            from app.models.direct_debit_mandate import DirectDebitMandate
            from app.models.money_transfer import MoneyTransfer
            from app.models.payment import Payment

            entity_id_int = int(request.entity_id)

            if request.entity_type == "Payment":
                payment = self.db.query(Payment).filter(Payment.id == entity_id_int).first()
                if not payment:
                    raise NotFoundError(message="Payment not found")
                account_id = payment.account_id
            elif request.entity_type == "MoneyTransfer":
                money_transfer = self.db.query(MoneyTransfer).filter(MoneyTransfer.id == entity_id_int).first()
                if not money_transfer:
                    raise NotFoundError(message="MoneyTransfer not found")
                account_id = money_transfer.account_id
            elif request.entity_type == "BalanceTransfer":
                balance_transfer = self.db.query(BalanceTransfer).filter(BalanceTransfer.id == entity_id_int).first()
                if not balance_transfer:
                    raise NotFoundError(message="BalanceTransfer not found")
                account_id = balance_transfer.account_id
            elif request.entity_type == "DirectDebitChangeRequest":
                dd_request = self.db.query(DirectDebitChangeRequest).filter(DirectDebitChangeRequest.id == entity_id_int).first()
                if not dd_request:
                    raise NotFoundError(message="DirectDebitChangeRequest not found")
                # Get account_id via mandate
                mandate = self.db.query(DirectDebitMandate).filter(DirectDebitMandate.id == dd_request.mandate_id).first()
                if not mandate:
                    raise NotFoundError(message="Associated mandate not found")
                account_id = mandate.account_id
            else:
                raise ValidationError(message=f"Unsupported entity_type: {request.entity_type}")

            # Build customer-visible state from tracker item
            customer_visible_state = {
                "entity_type": request.entity_type,
                "entity_id": request.entity_id,
                "title": tracker_item.title,
                "lifecycle_state": tracker_item.lifecycle_state,
                "status_label": tracker_item.status_label,
                "is_final": tracker_item.is_final,
                "last_updated_at": tracker_item.last_updated_at.isoformat(),
            }

            # Get synchronization record for entity
            sync_record = self.db.query(SynchronizationRecord).filter(
                SynchronizationRecord.entity_type == request.entity_type,
                SynchronizationRecord.entity_id == request.entity_id
            ).order_by(SynchronizationRecord.last_sync_at.desc()).first()

            # Get tracking events for entity
            events = self.db.query(TrackingEvent).filter(
                TrackingEvent.entity_type == request.entity_type,
                TrackingEvent.entity_id == request.entity_id
            ).order_by(TrackingEvent.occurred_at.asc()).all()

            # Get risk decision from entity (masked)
            # For now, return None as risk details are in separate tables
            # In a full implementation, we'd query the entity table for risk_decision
            risk_decision = None

        # Build lifecycle events
        lifecycle_events = [
            DiagnosticEvent(
                event_timestamp=event.occurred_at,
                event_type=event.event_type,
                status=event.status,
                source_system=None,  # Would come from event_data if stored
                source_event_reference=None,  # Would come from event_data if stored
                detail=event.event_data
            )
            for event in events
        ]

        # Build synchronization summary
        if sync_record:
            synchronization_summary = SynchronizationSummary(
                last_synchronized_at=sync_record.last_sync_at,
                sync_outcome=sync_record.sync_status,  # sync_status maps to sync_outcome
                freshness_status=None,  # Not stored in this model version
                retry_count=0  # Not stored in this model version
            )
        else:
            synchronization_summary = SynchronizationSummary(
                last_synchronized_at=None,
                sync_outcome=None,
                freshness_status=None,
                retry_count=0
            )

        # Build escalation context
        escalation_context = self._build_escalation_context(
            request.entity_type or "Account",
            customer_visible_state,
            risk_decision,
            events
        )

        # Write audit event BEFORE returning (synchronous)
        audit_log = self.audit_service.record(
            user_id=support_user_id,
            action="support_lookup",
            entity_type=request.entity_type or "Account",
            entity_id=account_id,
            severity="info",
            correlation_id=correlation_id,
            details={
                "verification_reference": request.verification_reference,
                "lookup_reason": request.lookup_reason,
                "entity_type": request.entity_type,
                "entity_id": request.entity_id,
            },
            retention_class="access_2y"
        )

        return DiagnosticLookupResponse(
            lookup_id=str(audit_log.id),
            customer_visible_state=customer_visible_state,
            lifecycle_events=lifecycle_events,
            synchronization_summary=synchronization_summary,
            risk_decision=risk_decision,
            escalation_context=escalation_context
        )

    def operational_summary(self, window_minutes: int = 60) -> OperationalSummaryResponse:
        """
        Get operational summary with aggregated metrics.

        Args:
            window_minutes: Time window for aggregation (5-1440 minutes)

        Returns:
            OperationalSummaryResponse with aggregated metrics

        Raises:
            ValidationError: If window_minutes is out of range
        """
        if window_minutes < 5 or window_minutes > 1440:
            raise ValidationError(message="window_minutes must be between 5 and 1440")
        
        window_start = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        # Query auth failures from audit logs
        auth_failures = self.db.query(func.count(AuditLog.id)).filter(
            AuditLog.action == "auth_failed",
            AuditLog.occurred_at >= window_start
        ).scalar() or 0
        
        total_auth_attempts = self.db.query(func.count(AuditLog.id)).filter(
            AuditLog.action.in_(["auth_success", "auth_failed"]),
            AuditLog.occurred_at >= window_start
        ).scalar() or 0
        
        auth_failure_rate = (auth_failures / total_auth_attempts * 100) if total_auth_attempts > 0 else 0.0

        # Query API errors from audit logs
        api_errors = self.db.query(func.count(AuditLog.id)).filter(
            AuditLog.action == "api_error",
            AuditLog.occurred_at >= window_start
        ).scalar() or 0
        
        total_api_calls = self.db.query(func.count(AuditLog.id)).filter(
            AuditLog.action.in_(["api_success", "api_error"]),
            AuditLog.occurred_at >= window_start
        ).scalar() or 0
        
        api_error_rate = (api_errors / total_api_calls * 100) if total_api_calls > 0 else 0.0
        
        # API latency - would come from metrics store in production
        api_latency_p95 = 0.0

        # Count stale accounts based on sync records
        stale_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
        stale_account_count = self.db.query(func.count(func.distinct(SynchronizationRecord.entity_id))).filter(
            SynchronizationRecord.entity_type == "account",
            SynchronizationRecord.last_sync_at < stale_threshold
        ).scalar() or 0

        # Invalid synchronized record rate
        failed_syncs = self.db.query(func.count(SynchronizationRecord.id)).filter(
            SynchronizationRecord.sync_status == "failed",
            SynchronizationRecord.updated_at >= window_start
        ).scalar() or 0
        
        total_syncs = self.db.query(func.count(SynchronizationRecord.id)).filter(
            SynchronizationRecord.updated_at >= window_start
        ).scalar() or 0
        
        invalid_synchronized_record_rate = (failed_syncs / total_syncs * 100) if total_syncs > 0 else 0.0

        # Top failure categories from audit logs
        top_failures = self.db.query(
            AuditLog.action,
            func.count(AuditLog.id).label("count")
        ).filter(
            AuditLog.action.like("%_failed"),
            AuditLog.occurred_at >= window_start
        ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).limit(5).all()
        
        top_failure_categories = [
            {"category": action, "count": count}
            for action, count in top_failures
        ]

        return OperationalSummaryResponse(
            window_minutes=window_minutes,
            auth_failure_rate=auth_failure_rate,
            api_error_rate=api_error_rate,
            api_latency_p95=api_latency_p95,
            stale_account_count=stale_account_count,
            invalid_synchronized_record_rate=invalid_synchronized_record_rate,
            top_failure_categories=top_failure_categories
        )

    def _build_escalation_context(
        self,
        entity_type: str,
        customer_visible_state: Dict[str, Any],
        risk_decision: Optional[RiskDecision],
        events: List[TrackingEvent]
    ) -> EscalationContext:
        """
        Build escalation context with recommended route.

        Args:
            entity_type: Entity type
            customer_visible_state: Customer-visible state dict
            risk_decision: Risk decision if available
            events: Tracking events

        Returns:
            EscalationContext with recommended route
        """
        recommended_route = "none"
        traceable_references = []
        summary = None

        # Extract correlation IDs from events
        for event in events:
            if event.correlation_id:
                traceable_references.append(f"correlation_id:{event.correlation_id}")

        # Determine recommended route based on entity type and state
        if entity_type == "Payment":
            is_final = customer_visible_state.get("is_final", False)
            status = customer_visible_state.get("lifecycle_state", "")
            if not is_final or status in ["Failed", "Restricted"]:
                recommended_route = "payment_operations"
                summary = "Payment requires payment operations review"

        elif entity_type == "MoneyTransfer":
            is_final = customer_visible_state.get("is_final", False)
            status = customer_visible_state.get("lifecycle_state", "")
            if not is_final or status in ["Failed", "Rejected", "Blocked"]:
                recommended_route = "transfer_operations"
                summary = "Money transfer requires transfer operations review"

        elif entity_type == "BalanceTransfer":
            is_final = customer_visible_state.get("is_final", False)
            status = customer_visible_state.get("lifecycle_state", "")
            if not is_final or status in ["Rejected", "ReviewRequired"]:
                recommended_route = "transfer_operations"
                summary = "Balance transfer requires transfer operations review"

        elif entity_type == "DirectDebitChangeRequest":
            is_final = customer_visible_state.get("is_final", False)
            status = customer_visible_state.get("lifecycle_state", "")
            if not is_final or status in ["Rejected", "Failed"]:
                recommended_route = "payment_operations"
                summary = "Direct debit change requires payment operations review"

        # Override with fraud/risk route if risk decision indicates review/restrict
        if risk_decision and risk_decision.decision in ["review", "restrict"]:
            recommended_route = "fraud_and_risk_review"
            summary = "Entity requires fraud and risk review"

        return EscalationContext(
            recommended_route=recommended_route,
            traceable_references=traceable_references,
            summary=summary
        )

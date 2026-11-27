"""
Status tracker service - unified lifecycle tracking across entities.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.status_tracker.status_tracker_models import TrackingEvent
from app.status_tracker.status_tracker_repository import StatusTrackerRepository
from app.status_tracker.status_tracker_schemas import (
    TrackerEscalation,
    TrackerFreshness,
    TrackerGuidance,
    TrackerItem,
    TrackerListResponse,
    TrackerMilestone,
)

logger = get_logger(__name__)


class StatusTrackingService:
    """Service for unified lifecycle tracking across entities."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = StatusTrackerRepository(db)

    def record_event(
        self,
        entity_type: str,
        entity_id: str,
        event_type: str,
        status: str,
        event_data: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> TrackingEvent:
        """Record a tracking event for entity lifecycle monitoring."""
        event = TrackingEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            status=status,
            event_data=event_data,
            correlation_id=correlation_id,
            occurred_at=datetime.now(timezone.utc)
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_tracker_view(
        self,
        account_id: int,
        status_group: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> TrackerListResponse:
        """
        Get unified tracker view aggregating trackable entities.

        Args:
            account_id: Account ID
            status_group: Optional filter: "unresolved" for non-final states
            limit: Maximum results per page
            offset: Pagination offset

        Returns:
            TrackerListResponse with aggregated tracker items
        """
        # Get entities from owning services
        payments = self.repository.get_payments_by_account(account_id, status_group)
        money_transfers = self.repository.get_money_transfers_by_account(account_id, status_group)
        balance_transfers = self.repository.get_balance_transfers_by_account(account_id, status_group)
        dd_requests = self.repository.get_direct_debit_change_requests_by_account(account_id, status_group)

        # Build tracker items
        items = []

        for payment in payments:
            items.append(self._build_payment_tracker_item(payment))

        for mt in money_transfers:
            items.append(self._build_money_transfer_tracker_item(mt))

        for bt in balance_transfers:
            items.append(self._build_balance_transfer_tracker_item(bt))

        for dd in dd_requests:
            items.append(self._build_dd_change_tracker_item(dd))

        # Sort by last_updated_at DESC
        items.sort(key=lambda x: x.last_updated_at, reverse=True)

        # Pagination
        total = len(items)
        paginated_items = items[offset:offset + limit]
        has_more = (offset + limit) < total

        # Compute unresolved count
        unresolved_count = sum(1 for item in items if not item.is_final)

        # Overall message when all sources unavailable or degraded
        overall_message = None
        if total == 0 and status_group == "unresolved":
            overall_message = "No unresolved actions to track at this time."
        elif total > 0 and all(item.escalation and item.escalation.is_escalated for item in items[:10]):
            overall_message = "Some actions may require attention. Please review escalated items."

        return TrackerListResponse(
            items=paginated_items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
            unresolved_count=unresolved_count,
            overall_message=overall_message,
        )

    def get_tracker_detail(
        self,
        entity_type: str,
        entity_id: str,
    ) -> dict | None:
        """
        Get detailed tracker item with timeline.

        Args:
            entity_type: Entity type (Payment, MoneyTransfer, BalanceTransfer, DirectDebitChangeRequest)
            entity_id: Entity ID

        Returns:
            Dict with tracker_item and milestones, or None if not found
        """
        # Get entity
        entity = self._get_entity_by_type_and_id(entity_type, entity_id)

        if not entity:
            logger.warning(f"Entity {entity_type}/{entity_id} not found")
            return None

        # Build tracker item
        if entity_type == "Payment":
            tracker_item = self._build_payment_tracker_item(entity)
        elif entity_type == "MoneyTransfer":
            tracker_item = self._build_money_transfer_tracker_item(entity)
        elif entity_type == "BalanceTransfer":
            tracker_item = self._build_balance_transfer_tracker_item(entity)
        elif entity_type == "DirectDebitChangeRequest":
            tracker_item = self._build_dd_change_tracker_item(entity)
        else:
            return None

        # Get tracking events (milestones)
        events = self.repository.get_tracking_events_for_entity(entity_type, entity_id)
        milestones = [
            TrackerMilestone(
                event_timestamp=event.occurred_at,
                milestone_label=event.status,
                detail=event.event_data,
            )
            for event in events
        ]

        # Timeline freshness
        timeline_freshness = TrackerFreshness(level="Current", as_of=datetime.now(timezone.utc))

        return {
            "tracker_item": tracker_item,
            "milestones": milestones,
            "timeline_freshness": timeline_freshness,
        }

    def _build_payment_tracker_item(self, payment) -> TrackerItem:
        """Build tracker item for payment."""
        is_final = payment.status in ["Completed", "Cancelled"]

        # Escalation check: unresolved beyond 30 minutes or Blocked
        escalation = None
        age_minutes = (datetime.now(timezone.utc) - payment.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 60
        if not is_final and (age_minutes > 30 or payment.status == "Restricted"):
            escalation = TrackerEscalation(
                is_escalated=True,
                reason="Payment unresolved beyond expected timeframe" if age_minutes > 30 else "Payment restricted",
                guidance="Please contact support if this persists.",
            )

        # Guidance for non-final/failed states
        guidance = None
        if payment.status == "Failed":
            guidance = TrackerGuidance(
                message_code="PMT_FAILED",
                message="Payment failed. Please retry or use a different payment method.",
                next_step="Retry payment",
            )
        elif payment.status == "Restricted":
            guidance = TrackerGuidance(
                message_code="PMT_RESTRICTED",
                message="Payment restricted due to security review.",
                next_step="Contact support",
            )

        return TrackerItem(
            entity_type="Payment",
            entity_id=str(payment.id),
            title=f"Payment of £{payment.amount:.2f}",
            lifecycle_state=payment.status,
            status_label=payment.status,
            is_final=is_final,
            amount=f"£{payment.amount:.2f}",
            last_updated_at=payment.updated_at,
            freshness=TrackerFreshness(level="Current", as_of=payment.updated_at),
            escalation=escalation,
            guidance=guidance,
            resource_path=f"/api/v1/payments/{payment.id}",
        )

    def _build_money_transfer_tracker_item(self, mt) -> TrackerItem:
        """Build tracker item for money transfer."""
        is_final = mt.status in ["Completed", "Cancelled"]

        # Escalation check: unresolved beyond 60 minutes or Blocked
        escalation = None
        age_minutes = (datetime.now(timezone.utc) - mt.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 60
        if not is_final and (age_minutes > 60 or mt.status == "Blocked"):
            escalation = TrackerEscalation(
                is_escalated=True,
                reason="Money transfer unresolved beyond expected timeframe" if age_minutes > 60 else "Transfer blocked",
                guidance="Please contact support for assistance.",
            )

        # Guidance
        guidance = None
        if mt.status == "Failed":
            guidance = TrackerGuidance(
                message_code="MT_FAILED",
                message="Money transfer failed.",
                next_step="Retry transfer",
            )
        elif mt.status == "Blocked":
            guidance = TrackerGuidance(
                message_code="MT_BLOCKED",
                message="Money transfer blocked due to security review.",
                next_step="Contact support",
            )

        return TrackerItem(
            entity_type="MoneyTransfer",
            entity_id=str(mt.id),
            title=f"Money Transfer of £{mt.amount:.2f}",
            lifecycle_state=mt.status,
            status_label=mt.status,
            is_final=is_final,
            amount=f"£{mt.amount:.2f}",
            last_updated_at=mt.updated_at,
            freshness=TrackerFreshness(level="Current", as_of=mt.updated_at),
            escalation=escalation,
            guidance=guidance,
            resource_path=f"/api/v1/money-transfers/{mt.id}",
        )

    def _build_balance_transfer_tracker_item(self, bt) -> TrackerItem:
        """Build tracker item for balance transfer."""
        is_final = bt.status in ["Completed", "Cancelled"]

        # Escalation check: unresolved beyond 24 hours or ReviewRequired
        escalation = None
        age_hours = (datetime.now(timezone.utc) - bt.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        if not is_final and (age_hours > 24 or bt.status == "ReviewRequired"):
            escalation = TrackerEscalation(
                is_escalated=True,
                reason="Balance transfer unresolved beyond expected timeframe" if age_hours > 24 else "Transfer requires review",
                guidance="Please allow additional time for review or contact support.",
            )

        # Guidance
        guidance = None
        if bt.status == "Rejected":
            guidance = TrackerGuidance(
                message_code="BT_REJECTED",
                message="Balance transfer rejected.",
                next_step="Review requirements and resubmit",
            )
        elif bt.status == "ReviewRequired":
            guidance = TrackerGuidance(
                message_code="BT_REVIEW_REQUIRED",
                message="Balance transfer requires additional review.",
                next_step="Wait for review completion",
            )

        return TrackerItem(
            entity_type="BalanceTransfer",
            entity_id=str(bt.id),
            title=f"Balance Transfer of £{bt.transfer_amount:.2f}",
            lifecycle_state=bt.status,
            status_label=bt.status,
            is_final=is_final,
            amount=f"£{bt.transfer_amount:.2f}",
            last_updated_at=bt.updated_at,
            freshness=TrackerFreshness(level="Current", as_of=bt.updated_at),
            escalation=escalation,
            guidance=guidance,
            resource_path=f"/api/v1/balance-transfers/{bt.id}",
        )

    def _build_dd_change_tracker_item(self, dd) -> TrackerItem:
        """Build tracker item for direct debit change request."""
        is_final = dd.status in ["Completed", "Cancelled"]

        # Escalation check: unresolved beyond 24 hours
        escalation = None
        age_hours = (datetime.now(timezone.utc) - dd.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        if not is_final and age_hours > 24:
            escalation = TrackerEscalation(
                is_escalated=True,
                reason="Direct debit change unresolved beyond expected timeframe",
                guidance="Please contact support for assistance.",
            )

        # Guidance
        guidance = None
        if dd.status == "Rejected":
            guidance = TrackerGuidance(
                message_code="DD_REJECTED",
                message="Direct debit change rejected.",
                next_step="Review requirements and resubmit",
            )

        return TrackerItem(
            entity_type="DirectDebitChangeRequest",
            entity_id=str(dd.id),
            title="Direct Debit Change Request",
            lifecycle_state=dd.status,
            status_label=dd.status,
            is_final=is_final,
            amount=None,
            last_updated_at=dd.updated_at,
            freshness=TrackerFreshness(level="Current", as_of=dd.updated_at),
            escalation=escalation,
            guidance=guidance,
            resource_path=f"/api/v1/direct-debits/change-requests/{dd.id}",
        )

    def _get_entity_by_type_and_id(self, entity_type: str, entity_id: str):
        """Get entity by type and ID."""
        from app.models.balance_transfer import BalanceTransfer
        from app.models.direct_debit_change_request import DirectDebitChangeRequest
        from app.models.money_transfer import MoneyTransfer
        from app.models.payment import Payment

        entity_id_int = int(entity_id)

        if entity_type == "Payment":
            return self.db.query(Payment).filter(Payment.id == entity_id_int).first()
        elif entity_type == "MoneyTransfer":
            return self.db.query(MoneyTransfer).filter(MoneyTransfer.id == entity_id_int).first()
        elif entity_type == "BalanceTransfer":
            return self.db.query(BalanceTransfer).filter(BalanceTransfer.id == entity_id_int).first()
        elif entity_type == "DirectDebitChangeRequest":
            return self.db.query(DirectDebitChangeRequest).filter(DirectDebitChangeRequest.id == entity_id_int).first()

        return None

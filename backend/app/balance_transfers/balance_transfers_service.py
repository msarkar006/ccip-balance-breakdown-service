"""
Balance transfer service - business logic for balance transfer tracking and initiation.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.adapters.balance_transfer_rail_adapter import (
    BalanceTransferRailAdapter,
    StubBalanceTransferRailAdapter,
)
from app.adapters.fraud_risk_adapter import FraudAndRiskAdapter, StubFraudAndRiskAdapter
from app.audit.audit_service import AuditService
from app.balance_transfers.balance_transfers_repository import BalanceTransfersRepository
from app.balance_transfers.balance_transfers_schemas import (
    BalanceTransferDetailResponse,
    BalanceTransferInitiationRequest,
    BalanceTransferInitiationResponse,
    BalanceTransferListItem,
    BalanceTransferListResponse,
    GuidanceInfo,
    PromotionalContext,
    SourceLink,
    TrackerMilestone,
)
from app.core.errors import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.pipeline import HighRiskWritePipeline
from app.models.balance_category import BalanceCategory
from app.models.balance_transfer import BalanceTransfer
from app.models.credit_card_account import CreditCardAccount
from app.models.offer import Offer
from app.models.tracking_event import TrackingEvent
from app.status_tracker.status_tracker_service import StatusTrackingService

logger = get_logger(__name__)


class BalanceTransferService:
    """Service for balance transfer tracking (read-only)."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = BalanceTransfersRepository(db)

    def get_history(
        self,
        account_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> BalanceTransferListResponse:
        """
        Get paginated balance transfer history for account.

        Args:
            account_id: Account ID
            limit: Maximum number of results (default 10)
            offset: Number of results to skip (default 0)

        Returns:
            BalanceTransferListResponse with paginated transfers
        """
        transfers, total = self.repository.get_by_account(
            account_id=account_id,
            limit=limit,
            offset=offset
        )

        items = [
            BalanceTransferListItem(
                id=t.id,
                external_transfer_id=t.external_transfer_id,
                transfer_amount=t.transfer_amount,
                promotional_rate=t.promotional_rate,
                status=t.status,
                requested_on=t.created_at,
                processed_at=t.processed_at,
            )
            for t in transfers
        ]

        return BalanceTransferListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )

    def get_detail(self, transfer_id: int, account_id: int) -> BalanceTransferDetailResponse:
        """
        Get detailed balance transfer with timeline, promotional context, and guidance.

        Args:
            transfer_id: Balance transfer ID
            account_id: Account ID for ownership verification

        Returns:
            BalanceTransferDetailResponse with full transfer detail

        Raises:
            NotFoundError: If transfer not found or does not belong to account
        """
        transfer = self.repository.get_by_id(transfer_id)

        if not transfer or transfer.account_id != account_id:
            raise NotFoundError("Balance transfer not found")

        # Build timeline from tracking events
        events = self.repository.get_tracking_events(transfer_id)
        timeline = [
            TrackerMilestone(
                event_type=e.event_type,
                status=e.status,
                occurred_at=e.occurred_at,
                event_data=e.event_data,
            )
            for e in events
        ]

        # Build promotional context
        promotional_context = None
        if transfer.promotional_rate is not None and transfer.promotional_period_months:
            promo_start_date = transfer.processed_at or transfer.created_at
            promo_end_date = promo_start_date + timedelta(days=transfer.promotional_period_months * 30)

            promotional_context = PromotionalContext(
                promo_rate=transfer.promotional_rate,
                promo_start_date=promo_start_date,
                promo_end_date=promo_end_date,
                revert_rate=None,  # Could be derived from account standard APR
            )

        # Build source link to balance category
        source_link = None
        linked_category = self.db.query(BalanceCategory).filter(
            BalanceCategory.source_balance_transfer_id == transfer.id
        ).first()

        if linked_category:
            source_link = SourceLink(
                source_type="BalanceTransfer",
                source_id=transfer.id,
                source_reference=transfer.external_transfer_id,
                category_id=linked_category.id,
                category_name=linked_category.category_name,
            )

        # Build guidance for Rejected or unresolved states
        guidance = None
        if transfer.status == "Rejected":
            guidance = GuidanceInfo(
                message_code="BT_REJECTED",
                message="This balance transfer was rejected. Please review the rejection reason and consider resubmitting with updated information.",
                next_step="Contact customer service for details or submit a new transfer request.",
            )
        elif transfer.status == "ReviewRequired":
            guidance = GuidanceInfo(
                message_code="BT_REVIEW_REQUIRED",
                message="Your balance transfer is under review. We will update you once the review is complete.",
                next_step="No action needed. We will notify you when the review is complete.",
            )

        return BalanceTransferDetailResponse(
            id=transfer.id,
            account_id=transfer.account_id,
            external_transfer_id=transfer.external_transfer_id,
            transfer_amount=transfer.transfer_amount,
            status=transfer.status,
            requested_on=transfer.created_at,
            processed_at=transfer.processed_at,
            timeline=timeline,
            promotional_context=promotional_context,
            source_link=source_link,
            guidance=guidance,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at,
        )

    def initiate_transfer(
        self,
        request: BalanceTransferInitiationRequest,
        user_id: int,
        step_up_verified_at: Optional[datetime]
    ) -> BalanceTransferInitiationResponse:
        """
        Initiate a balance transfer using HighRiskWritePipeline.

        Args:
            request: Initiation request
            user_id: Acting user ID
            step_up_verified_at: Step-up verification timestamp

        Returns:
            BalanceTransferInitiationResponse with outcome
        """
        # Verify step-up is valid (within 300 seconds)
        step_up_verified = False
        if step_up_verified_at:
            age_seconds = (datetime.utcnow() - step_up_verified_at).total_seconds()
            step_up_verified = age_seconds <= 300

        pipeline = BalanceTransferInitiationPipeline(
            db=self.db,
            risk_adapter=StubFraudAndRiskAdapter(),
            rail_adapter=StubBalanceTransferRailAdapter(),
            audit_service=AuditService(self.db),
            tracker_service=StatusTrackingService(self.db),
        )

        result = pipeline.execute(
            account_id=request.account_id,
            user_id=user_id,
            step_up_verified=step_up_verified,
            idempotency_key=request.idempotency_key,
            payload={
                "offer_code": request.offer_code,
                "transfer_amount": float(request.transfer_amount),
                "external_card_last4": request.external_card_last4,
                "provider_name": request.provider_name,
            }
        )

        return BalanceTransferInitiationResponse(
            id=result["id"],
            external_transfer_id=result["external_transfer_id"],
            transfer_amount=Decimal(str(result["transfer_amount"])),
            status=result["status"],
            guidance=result.get("guidance"),
            idempotent_replay=result.get("idempotent_replay", False),
        )


class BalanceTransferInitiationPipeline(HighRiskWritePipeline):
    """Pipeline for balance transfer initiation."""

    def __init__(
        self,
        db: Session,
        risk_adapter: FraudAndRiskAdapter,
        rail_adapter: BalanceTransferRailAdapter,
        audit_service: AuditService,
        tracker_service: StatusTrackingService,
    ):
        super().__init__(db)
        self.risk_adapter = risk_adapter
        self.rail_adapter = rail_adapter
        self.audit_service = audit_service
        self.tracker_service = tracker_service
        self.repository = BalanceTransfersRepository(db)

    def _check_ownership(self, account_id: int, user_id: int) -> None:
        """Verify user owns the account."""
        from app.models.app_user import AppUser
        from app.models.customer import Customer

        user = self.db.query(AppUser).filter(AppUser.id == user_id).first()
        if not user:
            raise AuthorizationError("User not found")

        # Superusers can perform any operation
        if user.is_superuser:
            return

        # Verify account exists and belongs to user's customer
        account = self.db.query(CreditCardAccount).filter(
            CreditCardAccount.id == account_id
        ).first()

        if not account:
            raise NotFoundError("Account not found")

        customer = self.db.query(Customer).filter(
            Customer.id == account.customer_id
        ).first()

        if not customer or customer.email != user.email:
            raise AuthorizationError("Account does not belong to user")

    def _validate_schema(self, payload: Dict[str, Any]) -> None:
        """Additional schema validation."""
        if len(payload.get("external_card_last4", "")) != 4:
            raise ValidationError("External card last 4 must be exactly 4 digits")

    def _check_idempotency(
        self, account_id: int, idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """Check for existing transfer with same idempotency key."""
        existing = self.repository.get_by_idempotency_key(account_id, idempotency_key)

        if existing:
            return {
                "id": existing.id,
                "external_transfer_id": existing.external_transfer_id,
                "transfer_amount": float(existing.transfer_amount),
                "status": existing.status,
                "idempotent_replay": True,
            }

        return None

    def _validate_business_rules(
        self, account_id: int, payload: Dict[str, Any]
    ) -> None:
        """Validate business rules: offer eligibility, amount limits."""
        account = self.db.query(CreditCardAccount).filter(
            CreditCardAccount.id == account_id
        ).first()

        if not account:
            raise NotFoundError("Account not found")

        transfer_amount = Decimal(str(payload["transfer_amount"]))

        # Check amount > 0
        if transfer_amount <= 0:
            raise ValidationError("Transfer amount must be greater than 0")

        # Check amount <= available_credit
        if transfer_amount > account.available_credit:
            raise ValidationError(
                f"Transfer amount exceeds available credit (£{account.available_credit})"
            )

        # Check offer eligibility
        offer_code = payload.get("offer_code")
        if offer_code:
            offer = self.db.query(Offer).filter(
                Offer.account_id == account_id,
                Offer.offer_code == offer_code,
                Offer.offer_type == "BalanceTransfer",
                Offer.status.in_(["Available", "Active"])
            ).first()

            if not offer:
                raise ValidationError(
                    f"Offer {offer_code} is not available for this account"
                )

    def _get_risk_decision(
        self, account_id: int, user_id: int, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get risk decision from fraud/risk adapter."""
        return self.risk_adapter.assess_balance_transfer(
            account_id=account_id,
            user_id=user_id,
            amount=payload["transfer_amount"]
        )

    def _submit_to_source(
        self, account_id: int, payload: Dict[str, Any]
    ) -> str:
        """Submit to balance transfer rail."""
        return self.rail_adapter.submit_transfer(
            account_id=account_id,
            amount=Decimal(str(payload["transfer_amount"])),
            external_card_last4=payload["external_card_last4"],
            provider_name=payload["provider_name"]
        )

    def _commit_entity(
        self,
        account_id: int,
        idempotency_key: Optional[str],
        external_id: Optional[str],
        risk_decision: Dict[str, Any],
        payload: Dict[str, Any]
    ) -> int:
        """Atomically commit balance transfer and first tracking event."""
        # Determine status based on risk decision
        if risk_decision["allow"]:
            status = "Submitted"
        elif risk_decision.get("reason") == "review":
            status = "ReviewRequired"
        else:
            status = "Rejected"

        # Create balance transfer
        transfer = BalanceTransfer(
            account_id=account_id,
            external_transfer_id=external_id or f"BT-PENDING-{idempotency_key[:8]}",
            idempotency_key=idempotency_key,
            transfer_amount=Decimal(str(payload["transfer_amount"])),
            promotional_rate=None,  # To be populated when offer applied
            promotional_period_months=None,
            status=status,
            processed_at=datetime.utcnow() if status == "Submitted" else None,
        )

        transfer = self.repository.create(transfer)

        # Create first tracking event
        event = TrackingEvent(
            entity_type="BalanceTransfer",
            entity_id=str(transfer.id),
            event_type="transfer.initiated",
            status=status,
            occurred_at=datetime.utcnow(),
            event_data=None,
        )
        self.db.add(event)
        self.db.flush()

        return transfer.id

    def _publish_event(self, entity_id: int, risk_decision: Dict[str, Any]) -> None:
        """Publish servicing.balance_transfer.submitted event."""
        logger.info(
            "Published balance_transfer.submitted event",
            entity_id=entity_id,
            risk_allow=risk_decision["allow"]
        )

    def _write_audit(
        self, entity_id: int, user_id: int, risk_decision: Dict[str, Any]
    ) -> None:
        """Write audit log with financial_7y retention."""
        self.audit_service.record(
            user_id=user_id,
            action="balance_transfer_initiation",
            entity_type="BalanceTransfer",
            entity_id=entity_id,
            severity="normal",
            details={"risk_allow": risk_decision["allow"]},
            retention_class="financial_7y"
        )

    def _build_result(self, entity_id: int, risk_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Build result with outcome and guidance."""
        transfer = self.repository.get_by_id(entity_id)

        result: Dict[str, Any] = {
            "id": transfer.id,
            "external_transfer_id": transfer.external_transfer_id,
            "transfer_amount": float(transfer.transfer_amount),
            "status": transfer.status,
        }

        # Add guidance for Rejected or ReviewRequired
        if transfer.status == "Rejected":
            result["guidance"] = GuidanceInfo(
                message_code="BT_REJECTED",
                message="This balance transfer was rejected. Please review the offer terms and try again.",
                next_step="Contact customer service for assistance."
            )
        elif transfer.status == "ReviewRequired":
            result["guidance"] = GuidanceInfo(
                message_code="BT_REVIEW_REQUIRED",
                message="Your balance transfer is under review. We will update you once complete.",
                next_step="No action needed."
            )

        return result

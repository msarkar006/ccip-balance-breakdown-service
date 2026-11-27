"""
Payment service - business logic for payment history and tracking.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.adapters.fraud_risk_adapter import (
    FraudAndRiskAdapter,
    StubFraudAndRiskAdapter,
)
from app.adapters.payment_rail_adapter import (
    PaymentRailAdapter,
    StubPaymentRailAdapter,
)
from app.audit.audit_service import AuditService
from app.core.errors import AuthorizationError, NotFoundError, ValidationError
from app.core.pipeline import HighRiskWritePipeline
from app.direct_debits.direct_debits_service import DirectDebitService
from app.models.credit_card_account import CreditCardAccount
from app.models.tracking_event import TrackingEvent
from app.payments.payments_models import Payment
from app.payments.payments_repository import PaymentsRepository
from app.payments.payments_schemas import (
    PaymentDetailResponse,
    PaymentGuidanceResponse,
    PaymentInitiationResponse,
    PaymentListResponse,
    PaymentResponse,
    TrackerMilestone,
)
from app.sync.sync_service import FreshnessAndSyncService


class PaymentService:
    """Payment service for payment history retrieval and initiation."""

    # Non-final statuses that allow cancellation if scheduled in the future
    CANCELLABLE_STATUSES = {"Submitted", "Processing"}

    # Non-final or failed statuses that need guidance
    GUIDANCE_STATUSES = {"Processing", "Failed", "Restricted"}

    def __init__(
        self,
        db: Session,
        rail_adapter: Optional[PaymentRailAdapter] = None,
        risk_adapter: Optional[FraudAndRiskAdapter] = None
    ):
        self.db = db
        self.repository = PaymentsRepository(db)
        self.freshness_service = FreshnessAndSyncService()
        self.audit_service = AuditService(db)
        self.rail_adapter = rail_adapter or StubPaymentRailAdapter()
        self.risk_adapter = risk_adapter or StubFraudAndRiskAdapter()

    def get_payments(
        self,
        account_id: int,
        payment_type: Optional[str] = None,
        limit: int = 25,
        offset: int = 0
    ) -> PaymentListResponse:
        """
        Get paginated payment history.

        Args:
            account_id: Account ID to filter by
            payment_type: Optional payment type filter (Scheduled, OneOff, DirectDebitCollection)
            limit: Maximum items to return (1-100, default 25)
            offset: Number of items to skip

        Returns:
            PaymentListResponse with page envelope
        """
        # Validate pagination parameters
        limit = max(1, min(100, limit))
        offset = max(0, offset)

        # Get payments and total count
        payments, total = self.repository.get_payments_by_account(
            account_id=account_id,
            payment_type=payment_type,
            limit=limit,
            offset=offset
        )

        # Convert to response models
        items = [PaymentResponse.model_validate(pmt) for pmt in payments]

        # Compute has_more flag
        has_more = (offset + limit) < total

        # Empty state message
        empty_state_message = "No payments found for this account" if total == 0 else None

        # Get freshness (stub returns "Current")
        freshness_info = self.freshness_service.get_freshness()
        freshness = {
            "level": freshness_info.level,
            "as_of": freshness_info.as_of
        }

        return PaymentListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
            empty_state_message=empty_state_message,
            freshness=freshness
        )

    def get_payment_detail(self, payment_id: int) -> PaymentDetailResponse:
        """
        Get detailed payment with timeline and cancellation availability.

        Args:
            payment_id: Payment ID

        Returns:
            PaymentDetailResponse with timeline and guidance

        Raises:
            NotFoundError: If payment not found
        """
        # Get payment
        payment = self.repository.get_payment_by_id(payment_id)
        if not payment:
            raise NotFoundError(f"Payment {payment_id} not found")

        # Get tracking events
        events = self.repository.get_tracking_events_for_payment(payment_id)

        # Build timeline ordered by occurred_at ASC
        timeline = [
            TrackerMilestone(
                event_type=event.event_type,
                status=event.status,
                event_timestamp=event.occurred_at,
                description=event.event_data
            )
            for event in events
        ]

        # Determine can_cancel based on status and payment type
        can_cancel = self._can_cancel_payment(payment)
        cancellation_message = self._get_cancellation_message(payment) if not can_cancel else None

        # Determine guidance for non-final/failed payments
        guidance = self._get_payment_guidance(payment) if payment.status in self.GUIDANCE_STATUSES else None

        return PaymentDetailResponse(
            payment=PaymentResponse.model_validate(payment),
            timeline=timeline,
            can_cancel=can_cancel,
            cancellation_message=cancellation_message,
            guidance=guidance
        )

    def cancel_payment(self, payment_id: int, user_id: int):
        """
        Cancel a payment.

        Args:
            payment_id: Payment ID to cancel
            user_id: User ID performing the cancellation

        Returns:
            PaymentCancellationResponse with cancellation details

        Raises:
            NotFoundError: If payment not found
            ValidationError: If payment cannot be cancelled (422)
        """
        from app.payments.payments_schemas import PaymentCancellationResponse
        from app.status_tracker.status_tracker_service import StatusTrackingService

        # Fetch payment
        payment = self.repository.get_payment_by_id(payment_id)
        if not payment:
            raise NotFoundError(f"Payment {payment_id} not found")

        # Check if payment can be cancelled
        if not self._can_cancel_payment(payment):
            message = self._get_cancellation_message(payment)
            raise ValidationError(message=message)

        # Store previous status before updating
        previous_status = payment.status

        # Update payment status to Cancelled
        payment.status = "Cancelled"
        payment.updated_at = datetime.now(timezone.utc)
        cancelled_at = payment.updated_at

        # Record audit event
        self.audit_service.record(
            user_id=user_id,
            action="payment_cancellation",
            entity_type="payment",
            entity_id=payment_id,
            severity="info",
            details={
                "payment_id": payment_id,
                "previous_status": previous_status
            },
            retention_class="financial_7y"
        )

        # Record tracking event
        tracking_service = StatusTrackingService(self.db)
        tracking_service.record_event(
            entity_type="Payment",
            entity_id=str(payment_id),
            event_type="payment_cancelled",
            status="Cancelled",
            event_data="Payment cancelled by customer"
        )

        # Commit changes
        self.db.commit()
        self.db.refresh(payment)

        # Build and return response
        return PaymentCancellationResponse(
            payment_id=payment.id,
            status=payment.status,
            message="Payment cancelled successfully",
            cancelled_at=cancelled_at
        )

    def _can_cancel_payment(self, payment: Payment) -> bool:
        """
        Determine if payment can be cancelled.

        Rules:
        - Only Submitted or Processing payments can be cancelled
        - Only if not yet submitted to rail (stub: check scheduled_date in future)
        """
        if payment.status not in self.CANCELLABLE_STATUSES:
            return False

        # Stub logic: if scheduled_date exists and is in the future, can cancel
        # In production: check if submitted to rail
        if payment.scheduled_date:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            # Remove timezone info for comparison if needed
            scheduled = payment.scheduled_date
            if scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=timezone.utc)
            return scheduled > now

        # For immediate payments (no scheduled_date), cannot cancel if already Processing
        return payment.status == "Submitted"

    def _get_cancellation_message(self, payment: Payment) -> str:
        """Get explanation for why payment cannot be cancelled."""
        if payment.status in {"Completed", "Cancelled"}:
            return f"Payment already {payment.status.lower()}"
        elif payment.status == "Failed":
            return "Failed payment cannot be cancelled"
        elif payment.status == "Restricted":
            return "Restricted payment cannot be cancelled"
        elif payment.status == "Processing" and not payment.scheduled_date:
            return "Payment already processing"
        else:
            return "Payment cannot be cancelled at this time"

    def _get_payment_guidance(self, payment: Payment) -> dict:
        """
        Get next-step guidance for non-final/failed payments.

        Returns guidance object with message_code, message, next_step.
        """
        if payment.status == "Processing":
            return {
                "message_code": "payment_processing",
                "message": "Your payment is being processed. This usually completes within 1 business day.",
                "next_step": "Check back later for updates"
            }
        elif payment.status == "Failed":
            return {
                "message_code": "payment_failed",
                "message": "Your payment could not be completed. Please try again or contact support.",
                "next_step": "Submit a new payment or contact support"
            }
        elif payment.status == "Restricted":
            return {
                "message_code": "payment_restricted",
                "message": "This payment requires additional review. Our team will contact you if needed.",
                "next_step": "Wait for notification or contact support"
            }
        else:
            return {
                "message_code": "payment_pending",
                "message": "Your payment is pending confirmation.",
                "next_step": "Check back for updates"
            }

    def initiate_payment(
        self,
        account_id: int,
        amount: Decimal,
        currency: str,
        payment_method: str,
        scheduled_date: Optional[datetime],
        idempotency_key: str,
        user_id: int,
        step_up_verified: bool
    ) -> PaymentInitiationResponse:
        """
        Initiate a one-off or scheduled payment via HighRiskWritePipeline.

        Args:
            account_id: Account ID
            amount: Payment amount
            currency: Currency code
            payment_method: Payment method
            scheduled_date: Optional scheduled date
            idempotency_key: Idempotency key
            user_id: User ID
            step_up_verified: Whether step-up auth has been performed

        Returns:
            PaymentInitiationResponse with outcome and guidance
        """
        # Build pipeline
        pipeline = PaymentInitiationPipeline(
            db=self.db,
            repository=self.repository,
            audit_service=self.audit_service,
            rail_adapter=self.rail_adapter,
            risk_adapter=self.risk_adapter
        )

        payload = {
            "amount": float(amount),
            "currency": currency,
            "payment_method": payment_method,
            "scheduled_date": scheduled_date
        }

        result = pipeline.execute(
            account_id=account_id,
            user_id=user_id,
            step_up_verified=step_up_verified,
            idempotency_key=idempotency_key,
            payload=payload
        )

        # Build response
        payment = result["payment"]
        response = PaymentInitiationResponse(
            id=payment.id,
            account_id=payment.account_id,
            external_payment_id=payment.external_payment_id,
            idempotency_key=payment.idempotency_key,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            scheduled_date=payment.scheduled_date,
            created_at=payment.created_at,
            guidance=result.get("guidance")
        )

        return response

    def get_payment_guidance(self, account_id: int) -> PaymentGuidanceResponse:
        """
        Get payment guidance with balance and direct debit coverage.

        Args:
            account_id: Account ID

        Returns:
            PaymentGuidanceResponse with guidance details
        """
        # Get account
        account = self.db.query(CreditCardAccount).filter(
            CreditCardAccount.id == account_id
        ).first()

        if not account:
            raise NotFoundError(f"Account {account_id} not found")

        # Get direct debit coverage from DirectDebitService
        dd_service = DirectDebitService(self.db)
        dd_coverage = dd_service.derive_coverage(
            account_id=account_id,
            minimum_payment=account.minimum_payment_due
        )

        return PaymentGuidanceResponse(
            minimum_payment=account.minimum_payment_due or Decimal("0.00"),
            due_date=account.payment_due_date,
            current_balance=account.current_balance,
            max_payment_amount=account.current_balance,
            direct_debit_coverage=dd_coverage.model_dump()
        )


class PaymentInitiationPipeline(HighRiskWritePipeline):
    """Pipeline for payment initiation."""

    def __init__(
        self,
        db: Session,
        repository: PaymentsRepository,
        audit_service: AuditService,
        rail_adapter: PaymentRailAdapter,
        risk_adapter: FraudAndRiskAdapter
    ):
        super().__init__(db)
        self.repository = repository
        self.audit_service = audit_service
        self.rail_adapter = rail_adapter
        self.risk_adapter = risk_adapter

    def _check_ownership(self, account_id: int, user_id: int) -> None:
        """Verify user owns the account."""
        from app.models.app_user import AppUser
        from app.models.customer import Customer
        
        # Get the user
        user = self.db.query(AppUser).filter(AppUser.id == user_id).first()
        if not user:
            raise AuthorizationError(message="User not found")
        
        # Get the account with its customer
        account = self.db.query(CreditCardAccount).filter(
            CreditCardAccount.id == account_id
        ).first()

        if not account:
            raise AuthorizationError(
                message=f"Account {account_id} not found or not owned by user"
            )
        
        # Verify the account's customer email matches the user's email
        customer = self.db.query(Customer).filter(
            Customer.id == account.customer_id
        ).first()
        
        if not customer or customer.email != user.email:
            raise AuthorizationError(
                message=f"Account {account_id} not owned by user"
            )

        # Store for business rules validation
        self._account = account

    def _validate_schema(self, payload: Dict[str, Any]) -> None:
        """Validate schema beyond Pydantic."""
        amount = payload.get("amount")

        if amount is None or amount <= 0:
            raise ValidationError(message="Payment amount must be greater than 0")

    def _check_idempotency(
        self, account_id: int, idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """Check for existing payment with same idempotency key."""
        existing = self.repository.get_payment_by_idempotency(
            account_id, idempotency_key
        )

        if existing:
            return {"payment": existing}

        return None

    def _validate_business_rules(
        self, account_id: int, payload: Dict[str, Any]
    ) -> None:
        """Validate business rules."""
        amount = Decimal(str(payload["amount"]))

        # Check amount does not exceed current balance
        if amount > self._account.current_balance:
            raise ValidationError(
                message=f"Payment amount £{amount} exceeds current balance £{self._account.current_balance}"
            )

    def _get_risk_decision(
        self, account_id: int, user_id: int, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get risk decision from adapter."""
        return self.risk_adapter.assess_payment(
            account_id=account_id,
            user_id=user_id,
            amount=payload["amount"],
            currency=payload["currency"]
        )

    def _submit_to_source(
        self, account_id: int, payload: Dict[str, Any]
    ) -> str:
        """Submit to payment rail."""
        return self.rail_adapter.submit_payment(
            account_id=account_id,
            amount=Decimal(str(payload["amount"])),
            currency=payload["currency"],
            payment_method=payload["payment_method"]
        )

    def _commit_entity(
        self,
        account_id: int,
        idempotency_key: Optional[str],
        external_id: Optional[str],
        risk_decision: Dict[str, Any],
        payload: Dict[str, Any]
    ) -> int:
        """Atomically commit payment and first tracking event."""
        # Determine status based on risk decision
        if risk_decision["allow"]:
            status = "Submitted"
        else:
            status = "Restricted"

        # Create payment
        payment = Payment(
            account_id=account_id,
            external_payment_id=external_id or f"PENDING-{idempotency_key[:8]}",
            idempotency_key=idempotency_key,
            payment_method=payload["payment_method"],
            amount=Decimal(str(payload["amount"])),
            currency=payload["currency"],
            status=status,
            scheduled_date=payload.get("scheduled_date"),
            processed_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        payment = self.repository.create_payment(payment)

        # Create first tracking event
        event = TrackingEvent(
            entity_type="Payment",
            entity_id=str(payment.id),
            event_type="payment_initiated",
            status=status,
            event_data=f"Payment {status.lower()}",
            occurred_at=datetime.now(timezone.utc)
        )

        self.repository.create_tracking_event(event)

        self.db.commit()

        # Store for result building
        self._payment = payment

        return payment.id

    def _publish_event(self, entity_id: int, risk_decision: Dict[str, Any]) -> None:
        """Publish servicing event (stub)."""
        # In production: publish servicing.payment.submitted event
        pass

    def _write_audit(
        self, entity_id: int, user_id: int, risk_decision: Dict[str, Any]
    ) -> None:
        """Write audit log for payment initiation."""
        self.audit_service.record(
            user_id=user_id,
            action="payment_initiation",
            entity_type="payment",
            entity_id=entity_id,
            severity="info",
            details={
                "payment_id": entity_id,
                "risk_allow": risk_decision["allow"]
            },
            retention_class="financial_7y"
        )

        self.db.commit()

    def _build_result(
        self, entity_id: int, risk_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build response result."""
        result = {"payment": self._payment}

        # Add guidance for restricted payments
        if not risk_decision["allow"]:
            result["guidance"] = {
                "message_code": "payment_restricted",
                "message": "This payment requires additional review.",
                "next_step": "Our team will contact you if needed"
            }

        return result

"""
Money transfer service - business logic for money transfer tracking and initiation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.adapters.fraud_risk_adapter import FraudAndRiskAdapter, StubFraudAndRiskAdapter
from app.adapters.money_transfer_rail_adapter import (
    MoneyTransferRailAdapter,
    StubMoneyTransferRailAdapter,
)
from app.audit.audit_service import AuditService
from app.core.errors import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.pipeline import HighRiskWritePipeline
from app.models.credit_card_account import CreditCardAccount
from app.models.money_transfer import MoneyTransfer
from app.models.tracking_event import TrackingEvent
from app.money_transfers.money_transfers_repository import MoneyTransfersRepository
from app.money_transfers.money_transfers_schemas import (
    GuidanceInfo,
    MoneyTransferDetailResponse,
    MoneyTransferInitiationRequest,
    MoneyTransferInitiationResponse,
    MoneyTransferListItem,
    MoneyTransferListResponse,
    PayeeInfo,
    PayeeListItem,
    PayeeListResponse,
    TrackerMilestone,
)
from app.status_tracker.status_tracker_service import StatusTrackingService

logger = get_logger(__name__)


class MoneyTransferService:
    """Service for money transfer tracking and initiation."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = MoneyTransfersRepository(db)

    def get_history(
        self,
        account_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> MoneyTransferListResponse:
        """
        Get paginated money transfer history for account.

        Args:
            account_id: Account ID
            limit: Maximum number of results (default 10)
            offset: Number of results to skip (default 0)

        Returns:
            MoneyTransferListResponse with paginated transfers
        """
        transfers, total = self.repository.get_by_account(
            account_id=account_id,
            limit=limit,
            offset=offset
        )

        items = []
        for t in transfers:
            payee = self.repository.get_payee(t.payee_id)
            payee_name = payee.payee_name if payee else "Unknown"

            items.append(
                MoneyTransferListItem(
                    id=t.id,
                    external_transfer_id=t.external_transfer_id,
                    payee_name=payee_name,
                    amount=t.amount,
                    currency=t.currency,
                    status=t.status,
                    requested_on=t.created_at,
                    processed_at=t.processed_at,
                )
            )

        return MoneyTransferListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )

    def get_detail(self, transfer_id: int, account_id: int) -> MoneyTransferDetailResponse:
        """
        Get detailed money transfer with timeline and guidance.

        Args:
            transfer_id: Money transfer ID
            account_id: Account ID for ownership verification

        Returns:
            MoneyTransferDetailResponse with full transfer detail

        Raises:
            NotFoundError: If transfer not found or does not belong to account
        """
        transfer = self.repository.get_by_id(transfer_id)

        if not transfer or transfer.account_id != account_id:
            raise NotFoundError("Money transfer not found")

        # Get payee details
        payee = self.repository.get_payee(transfer.payee_id)
        if not payee:
            raise NotFoundError("Payee not found")

        payee_info = PayeeInfo(
            payee_id=payee.id,
            payee_name=payee.payee_name,
            account_number_masked=payee.account_number_masked,
            sort_code_masked=payee.sort_code_masked,
        )

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

        # Build guidance for non-final or failed states
        guidance = self._build_guidance(transfer.status)

        return MoneyTransferDetailResponse(
            id=transfer.id,
            account_id=transfer.account_id,
            external_transfer_id=transfer.external_transfer_id,
            payee=payee_info,
            amount=transfer.amount,
            currency=transfer.currency,
            fee_context=None,  # Fee context not available in demo
            status=transfer.status,
            requested_on=transfer.created_at,
            processed_at=transfer.processed_at,
            timeline=timeline,
            guidance=guidance,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at,
        )

    def get_payees(
        self,
        account_id: int,
        limit: int = 25,
        offset: int = 0
    ) -> PayeeListResponse:
        """
        Get paginated list of customer-owned payees.

        Args:
            account_id: Account ID
            limit: Maximum number of results (default 25)
            offset: Number of results to skip (default 0)

        Returns:
            PayeeListResponse with paginated payees
        """
        payees, total = self.repository.get_payees_by_account(
            account_id=account_id,
            limit=limit,
            offset=offset
        )

        items = [
            PayeeListItem(
                id=p.id,
                payee_name=p.payee_name,
                account_number_masked=p.account_number_masked,
                sort_code_masked=p.sort_code_masked,
                created_at=p.created_at,
            )
            for p in payees
        ]

        return PayeeListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )

    def initiate_transfer(
        self,
        request: MoneyTransferInitiationRequest,
        user_id: int,
        step_up_verified_at: Optional[datetime]
    ) -> MoneyTransferInitiationResponse:
        """
        Initiate a money transfer using HighRiskWritePipeline.

        Args:
            request: Initiation request
            user_id: Acting user ID
            step_up_verified_at: Step-up verification timestamp

        Returns:
            MoneyTransferInitiationResponse with outcome
        """
        # Verify step-up is valid (within 300 seconds)
        step_up_verified = False
        if step_up_verified_at:
            age_seconds = (datetime.utcnow() - step_up_verified_at).total_seconds()
            step_up_verified = age_seconds <= 300

        pipeline = MoneyTransferInitiationPipeline(
            db=self.db,
            risk_adapter=StubFraudAndRiskAdapter(),
            rail_adapter=StubMoneyTransferRailAdapter(),
            audit_service=AuditService(self.db),
            tracker_service=StatusTrackingService(self.db),
        )

        result = pipeline.execute(
            account_id=request.account_id,
            user_id=user_id,
            step_up_verified=step_up_verified,
            idempotency_key=request.idempotency_key,
            payload={
                "payee_id": request.payee_id,
                "amount": float(request.amount),
                "currency": request.currency,
            }
        )

        return MoneyTransferInitiationResponse(
            id=result["id"],
            external_transfer_id=result["external_transfer_id"],
            amount=Decimal(str(result["amount"])),
            currency=result["currency"],
            status=result["status"],
            guidance=result.get("guidance"),
            idempotent_replay=result.get("idempotent_replay", False),
        )

    def _build_guidance(self, status: str) -> Optional[GuidanceInfo]:
        """
        Build guidance for non-final or failed transfer states.

        Args:
            status: Transfer status

        Returns:
            GuidanceInfo if guidance applicable, None otherwise
        """
        if status == "Failed":
            return GuidanceInfo(
                message_code="MT_FAILED",
                message="This money transfer failed. The funds have not been debited from your account.",
                next_step="Please verify the payee details and try again, or contact customer service for assistance.",
            )
        elif status == "Rejected":
            return GuidanceInfo(
                message_code="MT_REJECTED",
                message="This money transfer was rejected. Please review the rejection reason.",
                next_step="Contact customer service for details or submit a new transfer request with corrected information.",
            )
        elif status == "Delayed":
            return GuidanceInfo(
                message_code="MT_DELAYED",
                message="This money transfer is experiencing delays. The transfer is still being processed.",
                next_step="No action needed. We will notify you when the transfer completes.",
            )
        elif status == "Blocked":
            return GuidanceInfo(
                message_code="MT_BLOCKED",
                message="This money transfer has been blocked for security review.",
                next_step="Contact customer service immediately to resolve the security review.",
            )

        return None


class MoneyTransferInitiationPipeline(HighRiskWritePipeline):
    """Pipeline for money transfer initiation."""

    def __init__(
        self,
        db: Session,
        risk_adapter: FraudAndRiskAdapter,
        rail_adapter: MoneyTransferRailAdapter,
        audit_service: AuditService,
        tracker_service: StatusTrackingService,
    ):
        super().__init__(db)
        self.risk_adapter = risk_adapter
        self.rail_adapter = rail_adapter
        self.audit_service = audit_service
        self.tracker_service = tracker_service
        self.repository = MoneyTransfersRepository(db)

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
        pass  # Pydantic handles schema validation

    def _check_idempotency(
        self, account_id: int, idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """Check for existing transfer with same idempotency key."""
        existing = self.repository.get_by_idempotency_key(account_id, idempotency_key)

        if existing:
            return {
                "id": existing.id,
                "external_transfer_id": existing.external_transfer_id,
                "amount": float(existing.amount),
                "currency": existing.currency,
                "status": existing.status,
                "idempotent_replay": True,
            }

        return None

    def _validate_business_rules(
        self, account_id: int, payload: Dict[str, Any]
    ) -> None:
        """Validate business rules: payee ownership, amount limits."""
        from app.models.payee import Payee

        account = self.db.query(CreditCardAccount).filter(
            CreditCardAccount.id == account_id
        ).first()

        if not account:
            raise NotFoundError("Account not found")

        # Check payee ownership
        payee_id = payload.get("payee_id")
        payee = self.db.query(Payee).filter(Payee.id == payee_id).first()

        if not payee:
            raise NotFoundError("Payee not found")

        if payee.account_id != account_id:
            raise AuthorizationError("Payee does not belong to this account")

        transfer_amount = Decimal(str(payload["amount"]))
        fee = Decimal("0.00")  # Stub fee

        # Check amount > 0
        if transfer_amount <= 0:
            raise ValidationError("Transfer amount must be greater than 0")

        # Check amount + fee <= available_credit
        if (transfer_amount + fee) > account.available_credit:
            raise ValidationError(
                f"Transfer amount plus fee exceeds available credit (£{account.available_credit})"
            )

    def _get_risk_decision(
        self, account_id: int, user_id: int, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get risk decision from fraud/risk adapter."""
        return self.risk_adapter.assess_money_transfer(
            account_id=account_id,
            user_id=user_id,
            amount=payload["amount"]
        )

    def _submit_to_source(
        self, account_id: int, payload: Dict[str, Any]
    ) -> str:
        """Submit to money transfer rail."""
        return self.rail_adapter.submit_transfer(
            account_id=account_id,
            payee_id=payload["payee_id"],
            amount=Decimal(str(payload["amount"])),
            currency=payload["currency"]
        )

    def _commit_entity(
        self,
        account_id: int,
        idempotency_key: Optional[str],
        external_id: Optional[str],
        risk_decision: Dict[str, Any],
        payload: Dict[str, Any]
    ) -> int:
        """Atomically commit money transfer and first tracking event."""
        # Determine status based on risk decision
        if risk_decision["allow"]:
            status = "Submitted"
        elif risk_decision.get("reason") == "review":
            status = "Blocked"
        else:
            status = "Rejected"

        # Create money transfer
        transfer = MoneyTransfer(
            account_id=account_id,
            payee_id=payload["payee_id"],
            external_transfer_id=external_id or f"MT-PENDING-{idempotency_key[:8]}",
            idempotency_key=idempotency_key,
            amount=Decimal(str(payload["amount"])),
            currency=payload["currency"],
            status=status,
            processed_at=datetime.utcnow() if status == "Submitted" else None,
        )

        transfer = self.repository.create(transfer)

        # Create first tracking event
        event = TrackingEvent(
            entity_type="MoneyTransfer",
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
        """Publish servicing.money_transfer.submitted event."""
        logger.info(
            "Published money_transfer.submitted event",
            entity_id=entity_id,
            risk_allow=risk_decision["allow"]
        )

    def _write_audit(
        self, entity_id: int, user_id: int, risk_decision: Dict[str, Any]
    ) -> None:
        """Write audit log with financial_7y retention."""
        self.audit_service.record(
            user_id=user_id,
            action="money_transfer_initiation",
            entity_type="MoneyTransfer",
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
            "amount": float(transfer.amount),
            "currency": transfer.currency,
            "status": transfer.status,
        }

        # Add guidance for Rejected or Blocked
        if transfer.status == "Rejected":
            result["guidance"] = GuidanceInfo(
                message_code="MT_REJECTED",
                message="This money transfer was rejected. Please review and try again.",
                next_step="Contact customer service for assistance."
            )
        elif transfer.status == "Blocked":
            result["guidance"] = GuidanceInfo(
                message_code="MT_BLOCKED",
                message="Your money transfer is under security review.",
                next_step="Contact customer service immediately."
            )

        return result

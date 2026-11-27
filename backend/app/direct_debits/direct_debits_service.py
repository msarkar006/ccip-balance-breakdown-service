"""
Direct debit service for mandate management and coverage derivation.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.adapters.direct_debit_rail_adapter import (
    DirectDebitRailAdapter,
    StubDirectDebitRailAdapter,
)
from app.adapters.fraud_risk_adapter import (
    FraudAndRiskAdapter,
    StubFraudAndRiskAdapter,
)
from app.audit.audit_service import AuditService
from app.core.errors import AuthorizationError, NotFoundError, ValidationError
from app.core.pipeline import HighRiskWritePipeline
from app.direct_debits.direct_debits_repository import DirectDebitRepository
from app.direct_debits.direct_debits_schemas import (
    ChangeRequestResponse,
    DirectDebitCoverageResponse,
    DirectDebitListItem,
    DirectDebitListResponse,
)
from app.models.credit_card_account import CreditCardAccount
from app.models.payment import Payment


class DirectDebitService:
    """Direct debit service for mandate visibility and change initiation."""

    def __init__(
        self,
        db: Session,
        rail_adapter: Optional[DirectDebitRailAdapter] = None,
        risk_adapter: Optional[FraudAndRiskAdapter] = None
    ):
        self.db = db
        self.repository = DirectDebitRepository(db)
        self.audit_service = AuditService(db)
        self.rail_adapter = rail_adapter or StubDirectDebitRailAdapter()
        self.risk_adapter = risk_adapter or StubFraudAndRiskAdapter()

    def get_mandates(self, account_id: int) -> DirectDebitListResponse:
        """
        Get all mandates for an account.
        
        Args:
            account_id: Account ID
            
        Returns:
            DirectDebitListResponse with mandate list
        """
        mandates = self.repository.get_mandates_by_account(account_id)

        items = [DirectDebitListItem.model_validate(m) for m in mandates]

        return DirectDebitListResponse(mandates=items)

    def derive_coverage(
        self,
        account_id: int,
        minimum_payment: Optional[Decimal] = None
    ) -> DirectDebitCoverageResponse:
        """
        Derive direct debit coverage for minimum payment.
        
        Logic:
        - expected_to_cover: Active mandate + recent collection + sufficient amount
        - not_expected_to_cover: Active mandate but insufficient amount or old data
        - cannot_be_confirmed: No active mandate or missing data
        
        Args:
            account_id: Account ID
            minimum_payment: Minimum payment threshold to check
            
        Returns:
            DirectDebitCoverageResponse with coverage assessment
        """
        # Get active mandate
        mandate = self.repository.get_active_mandate_by_account(account_id)

        if not mandate:
            return DirectDebitCoverageResponse(
                coverage_status="cannot_be_confirmed",
                manual_payment_may_be_required=True,
                reason="No active direct debit mandate found"
            )

        # Check mandate type and payment amount
        if mandate.mandate_type == "MinimumPayment":
            # MinimumPayment mandates are expected to cover minimum payment
            # Check if we have recent collection payment data
            recent_payment = self._get_latest_dd_collection_payment(account_id)

            if recent_payment and self._is_recent(recent_payment.created_at):
                return DirectDebitCoverageResponse(
                    coverage_status="expected_to_cover",
                    manual_payment_may_be_required=False,
                    reason="Active MinimumPayment mandate with recent collection"
                )
            else:
                return DirectDebitCoverageResponse(
                    coverage_status="cannot_be_confirmed",
                    manual_payment_may_be_required=True,
                    reason="Active mandate but no recent collection data"
                )

        elif mandate.mandate_type == "StatementBalance":
            # StatementBalance mandates are expected to cover everything
            return DirectDebitCoverageResponse(
                coverage_status="expected_to_cover",
                manual_payment_may_be_required=False,
                reason="Active StatementBalance mandate"
            )

        elif mandate.mandate_type == "FixedAmount":
            # FixedAmount needs comparison with minimum payment
            if not mandate.payment_amount or not minimum_payment:
                return DirectDebitCoverageResponse(
                    coverage_status="cannot_be_confirmed",
                    manual_payment_may_be_required=True,
                    reason="Missing payment amount data for comparison"
                )

            if mandate.payment_amount >= minimum_payment:
                return DirectDebitCoverageResponse(
                    coverage_status="expected_to_cover",
                    manual_payment_may_be_required=False,
                    reason=f"Fixed amount £{mandate.payment_amount} covers minimum payment"
                )
            else:
                return DirectDebitCoverageResponse(
                    coverage_status="not_expected_to_cover",
                    manual_payment_may_be_required=True,
                    reason=f"Fixed amount £{mandate.payment_amount} is less than minimum payment £{minimum_payment}"
                )

        else:
            return DirectDebitCoverageResponse(
                coverage_status="cannot_be_confirmed",
                manual_payment_may_be_required=True,
                reason="Unknown mandate type"
            )

    def initiate_change(
        self,
        mandate_id: int,
        change_type: str,
        new_payment_amount: Optional[Decimal],
        idempotency_key: str,
        user_id: int,
        step_up_verified: bool
    ) -> ChangeRequestResponse:
        """
        Initiate a direct debit mandate change via HighRiskWritePipeline.
        
        Args:
            mandate_id: Mandate ID
            change_type: Change type (Amend, Cancel, Reinstate)
            new_payment_amount: New payment amount for Amend
            idempotency_key: Idempotency key
            user_id: User ID
            step_up_verified: Whether step-up auth has been performed
            
        Returns:
            ChangeRequestResponse with change request details
        """
        # Get mandate to verify it exists and get account_id
        mandate = self.repository.get_mandate_by_id(mandate_id)
        if not mandate:
            raise NotFoundError(f"Mandate {mandate_id} not found")

        account_id = mandate.account_id

        # Build pipeline
        pipeline = DirectDebitChangePipeline(
            db=self.db,
            repository=self.repository,
            audit_service=self.audit_service,
            rail_adapter=self.rail_adapter,
            risk_adapter=self.risk_adapter
        )

        payload = {
            "mandate_id": mandate_id,
            "change_type": change_type,
            "new_payment_amount": float(new_payment_amount) if new_payment_amount else None
        }

        result = pipeline.execute(
            account_id=account_id,
            user_id=user_id,
            step_up_verified=step_up_verified,
            idempotency_key=idempotency_key,
            payload=payload
        )

        return ChangeRequestResponse.model_validate(result["change_request"])

    def _get_latest_dd_collection_payment(
        self, account_id: int
    ) -> Optional[Payment]:
        """Get latest direct debit collection payment for account."""
        return self.db.query(Payment).filter(
            Payment.account_id == account_id,
            Payment.payment_method == "DirectDebit"
        ).order_by(
            Payment.created_at.desc()
        ).first()

    def _is_recent(self, dt: datetime, days: int = 35) -> bool:
        """Check if datetime is within recent period (default 35 days)."""
        now = datetime.now(timezone.utc)
        # Handle timezone-naive datetimes
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        age = now - dt
        return age <= timedelta(days=days)


class DirectDebitChangePipeline(HighRiskWritePipeline):
    """Pipeline for direct debit change requests."""

    def __init__(
        self,
        db: Session,
        repository: DirectDebitRepository,
        audit_service: AuditService,
        rail_adapter: DirectDebitRailAdapter,
        risk_adapter: FraudAndRiskAdapter
    ):
        super().__init__(db)
        self.repository = repository
        self.audit_service = audit_service
        self.rail_adapter = rail_adapter
        self.risk_adapter = risk_adapter

    def execute(
        self,
        account_id: int,
        user_id: int,
        step_up_verified: bool,
        idempotency_key: Optional[str],
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute pipeline with mandate_id extracted early for idempotency check."""
        # Extract mandate_id from payload for idempotency check
        self._mandate_id = payload.get("mandate_id")
        return super().execute(account_id, user_id, step_up_verified, idempotency_key, payload)

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

    def _validate_schema(self, payload: Dict[str, Any]) -> None:
        """Validate schema beyond Pydantic."""
        change_type = payload.get("change_type")
        new_payment_amount = payload.get("new_payment_amount")

        if change_type not in ["Amend", "Cancel", "Reinstate"]:
            raise ValidationError(
                message=f"Invalid change_type: {change_type}"
            )

        if change_type == "Amend" and not new_payment_amount:
            raise ValidationError(
                message="new_payment_amount required for Amend change type"
            )

    def _check_idempotency(
        self, account_id: int, idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """Check for existing change request with same idempotency key."""
        # mandate_id is stored in _validate_business_rules, but we need it here
        # So we extract it from the payload that was passed to execute()
        mandate_id = getattr(self, "_mandate_id", None)
        if not mandate_id:
            # This shouldn't happen in normal flow, but return None safely
            return None

        existing = self.repository.get_change_request_by_idempotency(
            mandate_id, idempotency_key
        )

        if existing:
            return {"change_request": existing}

        return None

    def _validate_business_rules(
        self, account_id: int, payload: Dict[str, Any]
    ) -> None:
        """Validate business rules."""
        # Store mandate_id for idempotency check
        self._mandate_id = payload["mandate_id"]

        # Verify mandate exists
        mandate = self.repository.get_mandate_by_id(self._mandate_id)
        if not mandate:
            raise ValidationError(
                message=f"Mandate {self._mandate_id} not found"
            )

        # Verify mandate belongs to account
        if mandate.account_id != account_id:
            raise AuthorizationError(
                message="Mandate does not belong to specified account"
            )

    def _get_risk_decision(
        self, account_id: int, user_id: int, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get risk decision from adapter."""
        return self.risk_adapter.assess_direct_debit_change(
            account_id=account_id,
            user_id=user_id,
            change_type=payload["change_type"]
        )

    def _submit_to_source(
        self, account_id: int, payload: Dict[str, Any]
    ) -> str:
        """Submit to direct debit rail."""
        return self.rail_adapter.submit_change_request(
            mandate_id=payload["mandate_id"],
            change_type=payload["change_type"],
            new_amount=payload.get("new_payment_amount")
        )

    def _commit_entity(
        self,
        account_id: int,
        idempotency_key: Optional[str],
        external_id: Optional[str],
        risk_decision: Dict[str, Any],
        payload: Dict[str, Any]
    ) -> int:
        """Atomically commit change request."""
        # Determine status based on risk decision
        if risk_decision["allow"]:
            status = "Submitted"
        else:
            status = "Restricted"

        change_request = self.repository.create_change_request(
            mandate_id=payload["mandate_id"],
            change_type=payload["change_type"],
            new_payment_amount=payload.get("new_payment_amount"),
            idempotency_key=idempotency_key or "",  # Ensure not None
            status=status
        )

        self.db.commit()

        # Store for result building
        self._change_request = change_request

        return change_request.id

    def _publish_event(self, entity_id: int, risk_decision: Dict[str, Any]) -> None:
        """Publish servicing event (stub)."""
        # In production: publish to event bus
        pass

    def _write_audit(
        self, entity_id: int, user_id: int, risk_decision: Dict[str, Any]
    ) -> None:
        """Write audit log for change request."""
        self.audit_service.record(
            user_id=user_id,
            action="direct_debit_change",
            entity_type="direct_debit_change_request",
            entity_id=entity_id,
            severity="info",
            details={
                "change_request_id": entity_id,
                "risk_allow": risk_decision["allow"]
            },
            retention_class="financial_7y"
        )

        self.db.commit()

    def _build_result(
        self, entity_id: int, risk_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build response result."""
        return {
            "change_request": self._change_request,
            "risk_decision": risk_decision
        }

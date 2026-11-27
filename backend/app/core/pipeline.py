"""
HighRiskWritePipeline - template method class for high-risk write operations.

Implements the pipeline order:
1. ownership check
2. step-up 403
3. schema 422
4. idempotency lookup
5. business rules
6. risk decision
7. source submission
8. atomic commit + first tracking event
9. publish event + audit
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.errors import AuthorizationError


class HighRiskWritePipeline(ABC):
    """
    Template method class for high-risk write operations.
    
    Subclasses must implement each step in the pipeline.
    """

    def __init__(self, db: Session):
        self.db = db

    def execute(
        self,
        account_id: int,
        user_id: int,
        step_up_verified: bool,
        idempotency_key: Optional[str],
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the full high-risk write pipeline.
        
        Args:
            account_id: Target account ID
            user_id: Acting user ID
            step_up_verified: Whether step-up auth has been performed
            idempotency_key: Optional idempotency key
            payload: Request payload
            
        Returns:
            Result dictionary with outcome and guidance
            
        Raises:
            AuthorizationError: If ownership or step-up check fails
            ConflictError: If idempotency replay detected
            ValidationError: If business rules fail
        """
        # 1. Ownership check
        self._check_ownership(account_id, user_id)

        # 2. Step-up verification
        if not step_up_verified:
            raise AuthorizationError(
                message="Step-up authentication required for this operation"
            )

        # 3. Schema validation - already done by Pydantic, but we can add extra checks
        self._validate_schema(payload)

        # 4. Idempotency lookup
        if idempotency_key:
            existing = self._check_idempotency(account_id, idempotency_key)
            if existing:
                # Return existing result
                return existing

        # 5. Business rules validation
        self._validate_business_rules(account_id, payload)

        # 6. Risk decision
        risk_decision = self._get_risk_decision(account_id, user_id, payload)

        # 7. Source submission (if risk allows)
        if risk_decision["allow"]:
            external_id = self._submit_to_source(account_id, payload)
        else:
            external_id = None

        # 8. Atomic commit + first tracking event
        entity_id = self._commit_entity(
            account_id=account_id,
            idempotency_key=idempotency_key,
            external_id=external_id,
            risk_decision=risk_decision,
            payload=payload
        )

        # 9. Publish event + audit
        self._publish_event(entity_id, risk_decision)
        self._write_audit(entity_id, user_id, risk_decision)

        # Build result
        return self._build_result(entity_id, risk_decision)

    @abstractmethod
    def _check_ownership(self, account_id: int, user_id: int) -> None:
        """
        Verify user owns the account.
        
        Raises:
            AuthorizationError: If ownership check fails
        """
        pass

    @abstractmethod
    def _validate_schema(self, payload: Dict[str, Any]) -> None:
        """
        Additional schema validation beyond Pydantic.
        
        Raises:
            ValidationError: If schema validation fails
        """
        pass

    @abstractmethod
    def _check_idempotency(
        self, account_id: int, idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check for existing operation with same idempotency key.
        
        Returns:
            Existing result if found, None otherwise
        """
        pass

    @abstractmethod
    def _validate_business_rules(
        self, account_id: int, payload: Dict[str, Any]
    ) -> None:
        """
        Validate business rules.
        
        Raises:
            ValidationError: If business rules fail
        """
        pass

    @abstractmethod
    def _get_risk_decision(
        self, account_id: int, user_id: int, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get risk decision from fraud/risk adapter.
        
        Returns:
            Risk decision with 'allow' boolean and optional 'reason'
        """
        pass

    @abstractmethod
    def _submit_to_source(
        self, account_id: int, payload: Dict[str, Any]
    ) -> str:
        """
        Submit to external source system.
        
        Returns:
            External ID from source system
        """
        pass

    @abstractmethod
    def _commit_entity(
        self,
        account_id: int,
        idempotency_key: Optional[str],
        external_id: Optional[str],
        risk_decision: Dict[str, Any],
        payload: Dict[str, Any]
    ) -> int:
        """
        Atomically commit entity and first tracking event.
        
        Returns:
            Entity ID
        """
        pass

    @abstractmethod
    def _publish_event(self, entity_id: int, risk_decision: Dict[str, Any]) -> None:
        """Publish servicing event."""
        pass

    @abstractmethod
    def _write_audit(
        self, entity_id: int, user_id: int, risk_decision: Dict[str, Any]
    ) -> None:
        """Write audit log."""
        pass

    @abstractmethod
    def _build_result(
        self, entity_id: int, risk_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build response result.
        
        Returns:
            Result dictionary with outcome and guidance
        """
        pass

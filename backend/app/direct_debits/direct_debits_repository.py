"""
Direct debit repository for database operations.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.direct_debits.direct_debits_models import (
    DirectDebitChangeRequest,
    DirectDebitMandate,
)


class DirectDebitRepository:
    """Repository for direct debit operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_mandates_by_account(self, account_id: int) -> List[DirectDebitMandate]:
        """
        Get all mandates for an account.
        
        Args:
            account_id: Account ID
            
        Returns:
            List of DirectDebitMandate
        """
        return self.db.query(DirectDebitMandate).filter(
            DirectDebitMandate.account_id == account_id
        ).order_by(
            DirectDebitMandate.created_at.desc(),
            DirectDebitMandate.id.desc()
        ).all()

    def get_active_mandate_by_account(
        self, account_id: int
    ) -> Optional[DirectDebitMandate]:
        """
        Get active mandate for an account.
        
        Args:
            account_id: Account ID
            
        Returns:
            Active DirectDebitMandate or None
        """
        return self.db.query(DirectDebitMandate).filter(
            DirectDebitMandate.account_id == account_id,
            DirectDebitMandate.status == "Active"
        ).first()

    def get_mandate_by_id(self, mandate_id: int) -> Optional[DirectDebitMandate]:
        """
        Get mandate by ID.
        
        Args:
            mandate_id: Mandate ID
            
        Returns:
            DirectDebitMandate or None
        """
        return self.db.query(DirectDebitMandate).filter(
            DirectDebitMandate.id == mandate_id
        ).first()

    def get_change_request_by_idempotency(
        self, mandate_id: int, idempotency_key: str
    ) -> Optional[DirectDebitChangeRequest]:
        """
        Find existing change request by idempotency key.
        
        Args:
            mandate_id: Mandate ID
            idempotency_key: Idempotency key
            
        Returns:
            DirectDebitChangeRequest or None
        """
        return self.db.query(DirectDebitChangeRequest).filter(
            DirectDebitChangeRequest.mandate_id == mandate_id,
            DirectDebitChangeRequest.idempotency_key == idempotency_key
        ).first()

    def create_change_request(
        self,
        mandate_id: int,
        change_type: str,
        new_payment_amount: Optional[float],
        idempotency_key: str,
        status: str = "Submitted"
    ) -> DirectDebitChangeRequest:
        """
        Create a new change request.
        
        Args:
            mandate_id: Mandate ID
            change_type: Change type (Amend, Cancel, Reinstate)
            new_payment_amount: New payment amount for Amend
            idempotency_key: Idempotency key
            status: Initial status
            
        Returns:
            Created DirectDebitChangeRequest
        """
        change_request = DirectDebitChangeRequest(
            mandate_id=mandate_id,
            change_type=change_type,
            new_payment_amount=new_payment_amount,
            idempotency_key=idempotency_key,
            status=status,
            processed_at=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.db.add(change_request)
        self.db.flush()
        return change_request

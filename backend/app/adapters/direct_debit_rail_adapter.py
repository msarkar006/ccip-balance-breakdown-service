"""
Direct debit rail adapter for mandate change submission.
"""
import uuid
from abc import ABC, abstractmethod
from typing import Optional


class DirectDebitRailAdapter(ABC):
    """Adapter for direct debit rail submission."""

    @abstractmethod
    def submit_change_request(
        self,
        mandate_id: int,
        change_type: str,
        new_amount: Optional[float] = None
    ) -> str:
        """
        Submit mandate change request to external rail.
        
        Args:
            mandate_id: Mandate ID
            change_type: Change type (Amend, Cancel, Reinstate)
            new_amount: New payment amount for Amend
            
        Returns:
            External change request ID from rail
        """
        pass


class StubDirectDebitRailAdapter(DirectDebitRailAdapter):
    """Stub implementation that generates mock external IDs."""

    def submit_change_request(
        self,
        mandate_id: int,
        change_type: str,
        new_amount: Optional[float] = None
    ) -> str:
        """Stub: returns generated external change request ID."""
        return f"EXT-DDC-{uuid.uuid4().hex[:12].upper()}"

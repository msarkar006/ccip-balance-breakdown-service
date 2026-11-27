"""
Identity adapter for step-up verification.
"""
from abc import ABC, abstractmethod
from typing import Dict


class IdentityStepUpAdapter(ABC):
    """Adapter for identity step-up verification."""

    @abstractmethod
    def verify_step_up(
        self,
        user_id: int,
        scope: str,
        proof: str
    ) -> Dict[str, bool]:
        """
        Verify step-up authentication proof.
        
        Args:
            user_id: User ID
            scope: Step-up scope (payment, transfer, direct_debit_change, etc.)
            proof: Step-up proof token
            
        Returns:
            Dict with 'verified' boolean
        """
        pass


class StubIdentityStepUpAdapter(IdentityStepUpAdapter):
    """Stub implementation that always verifies."""

    def verify_step_up(
        self,
        user_id: int,
        scope: str,
        proof: str
    ) -> Dict[str, bool]:
        """Stub: always returns verified=True."""
        return {"verified": True}

"""
Payment rail adapter for payment submission.
"""
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal


class PaymentRailAdapter(ABC):
    """Adapter for payment rail submission."""

    @abstractmethod
    def submit_payment(
        self,
        account_id: int,
        amount: Decimal,
        currency: str,
        payment_method: str
    ) -> str:
        """
        Submit payment to external rail.
        
        Args:
            account_id: Account ID
            amount: Payment amount
            currency: Currency code
            payment_method: Payment method
            
        Returns:
            External payment ID from rail
        """
        pass


class StubPaymentRailAdapter(PaymentRailAdapter):
    """Stub implementation that generates mock external IDs."""

    def submit_payment(
        self,
        account_id: int,
        amount: Decimal,
        currency: str,
        payment_method: str
    ) -> str:
        """Stub: returns generated external payment ID."""
        return f"EXT-PMT-{uuid.uuid4().hex[:12].upper()}"

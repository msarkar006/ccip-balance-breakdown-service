"""
Money transfer rail adapter for transfer submission.
"""
from abc import ABC, abstractmethod
from decimal import Decimal


class MoneyTransferRailAdapter(ABC):
    """Adapter for money transfer rail submission."""

    @abstractmethod
    def submit_transfer(
        self,
        account_id: int,
        payee_id: int,
        amount: Decimal,
        currency: str
    ) -> str:
        """
        Submit money transfer to external rail.
        
        Args:
            account_id: Account ID
            payee_id: Payee ID
            amount: Transfer amount
            currency: Currency code
            
        Returns:
            External transfer ID from rail
        """
        pass


class StubMoneyTransferRailAdapter(MoneyTransferRailAdapter):
    """Stub implementation that generates mock external IDs."""

    def submit_transfer(
        self,
        account_id: int,
        payee_id: int,
        amount: Decimal,
        currency: str
    ) -> str:
        """Stub: generates a mock external transfer ID."""
        import uuid
        return f"MT-EXT-{uuid.uuid4().hex[:8].upper()}"

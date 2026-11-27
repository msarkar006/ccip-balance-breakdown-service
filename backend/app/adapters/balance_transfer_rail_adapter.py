"""
Balance transfer rail adapter for transfer submission.
"""
from abc import ABC, abstractmethod
from decimal import Decimal


class BalanceTransferRailAdapter(ABC):
    """Adapter for balance transfer rail submission."""

    @abstractmethod
    def submit_transfer(
        self,
        account_id: int,
        amount: Decimal,
        external_card_last4: str,
        provider_name: str
    ) -> str:
        """
        Submit balance transfer to external rail.
        
        Args:
            account_id: Account ID
            amount: Transfer amount
            external_card_last4: Last 4 digits of external card
            provider_name: Provider name
            
        Returns:
            External transfer ID from rail
        """
        pass


class StubBalanceTransferRailAdapter(BalanceTransferRailAdapter):
    """Stub implementation that generates mock external IDs."""

    def submit_transfer(
        self,
        account_id: int,
        amount: Decimal,
        external_card_last4: str,
        provider_name: str
    ) -> str:
        """Stub: generates a mock external transfer ID."""
        import uuid
        return f"BT-EXT-{uuid.uuid4().hex[:8].upper()}"

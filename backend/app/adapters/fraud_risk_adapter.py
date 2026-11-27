"""
Fraud and risk adapter for risk decisions.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class FraudAndRiskAdapter(ABC):
    """Adapter for fraud and risk control services."""

    @abstractmethod
    def assess_payment(
        self,
        account_id: int,
        user_id: int,
        amount: float,
        currency: str
    ) -> Dict[str, Any]:
        """
        Assess payment for fraud/risk.
        
        Args:
            account_id: Account ID
            user_id: User ID
            amount: Payment amount
            currency: Currency code
            
        Returns:
            Dict with 'allow' boolean and optional 'reason'
        """
        pass

    @abstractmethod
    def assess_direct_debit_change(
        self,
        account_id: int,
        user_id: int,
        change_type: str
    ) -> Dict[str, Any]:
        """
        Assess direct debit change for fraud/risk.
        
        Args:
            account_id: Account ID
            user_id: User ID
            change_type: Change type
            
        Returns:
            Dict with 'allow' boolean and optional 'reason'
        """
        pass

    @abstractmethod
    def assess_balance_transfer(
        self,
        account_id: int,
        user_id: int,
        amount: float
    ) -> Dict[str, Any]:
        """
        Assess balance transfer for fraud/risk.
        
        Args:
            account_id: Account ID
            user_id: User ID
            amount: Transfer amount
            
        Returns:
            Dict with 'allow' boolean and optional 'reason'
        """
        pass

    @abstractmethod
    def assess_money_transfer(
        self,
        account_id: int,
        user_id: int,
        amount: float
    ) -> Dict[str, Any]:
        """
        Assess money transfer for fraud/risk.
        
        Args:
            account_id: Account ID
            user_id: User ID
            amount: Transfer amount
            
        Returns:
            Dict with 'allow' boolean and optional 'reason'
        """
        pass


class StubFraudAndRiskAdapter(FraudAndRiskAdapter):
    """Stub implementation that allows all operations."""

    def assess_payment(
        self,
        account_id: int,
        user_id: int,
        amount: float,
        currency: str
    ) -> Dict[str, Any]:
        """Stub: always allows."""
        return {"allow": True}

    def assess_direct_debit_change(
        self,
        account_id: int,
        user_id: int,
        change_type: str
    ) -> Dict[str, Any]:
        """Stub: always allows."""
        return {"allow": True}

    def assess_balance_transfer(
        self,
        account_id: int,
        user_id: int,
        amount: float
    ) -> Dict[str, Any]:
        """Stub: always allows."""
        return {"allow": True}

    def assess_money_transfer(
        self,
        account_id: int,
        user_id: int,
        amount: float
    ) -> Dict[str, Any]:
        """Stub: always allows."""
        return {"allow": True}

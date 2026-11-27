"""
Accounts domain repository for database operations.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.accounts.accounts_models import CreditCard, CreditCardAccount
from app.core.logging import get_logger

logger = get_logger(__name__)


class AccountsRepository:
    """Repository for account-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_customer_accounts(self, customer_id: int) -> List[CreditCardAccount]:
        """
        Get all accounts for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            List of credit card accounts
        """
        return self.db.query(CreditCardAccount).filter(
            CreditCardAccount.customer_id == customer_id
        ).all()

    def get_account_by_id(self, account_id: int) -> Optional[CreditCardAccount]:
        """
        Get account by ID.

        Args:
            account_id: Account ID

        Returns:
            Account if found, None otherwise
        """
        return self.db.query(CreditCardAccount).filter(
            CreditCardAccount.id == account_id
        ).first()

    def get_account_cards(self, account_id: int) -> List[CreditCard]:
        """
        Get all cards for an account.

        Args:
            account_id: Account ID

        Returns:
            List of credit cards
        """
        return self.db.query(CreditCard).filter(
            CreditCard.account_id == account_id
        ).all()

    def verify_account_ownership(self, account_id: int, customer_id: int) -> bool:
        """
        Verify that an account belongs to a customer.

        Args:
            account_id: Account ID
            customer_id: Customer ID

        Returns:
            True if account belongs to customer, False otherwise
        """
        account = self.get_account_by_id(account_id)
        if not account:
            return False
        return account.customer_id == customer_id

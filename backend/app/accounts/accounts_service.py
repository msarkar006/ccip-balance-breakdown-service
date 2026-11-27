"""
Accounts domain service - business logic for account operations.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.accounts.accounts_repository import AccountsRepository
from app.accounts.accounts_schemas import (
    AccountListResponse,
    AccountOverviewResponse,
    AccountSelectionResponse,
    CreditCardDetail,
)
from app.auth.auth_repository import AuthRepository
from app.core.errors import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.middleware.auth import verify_account_ownership
from app.models.app_user import AppUser
from app.sync.sync_service import FreshnessAndSyncService

logger = get_logger(__name__)


class AccountOverviewService:
    """Service for account overview and multi-account context."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = AccountsRepository(db)
        self.auth_repo = AuthRepository(db)
        self.freshness_service = FreshnessAndSyncService()

    def list_accounts(self, customer_id: int) -> AccountListResponse:
        """
        List all accounts for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            List of accounts with basic information
        """
        accounts = self.repo.get_customer_accounts(customer_id)

        logger.info("Listed accounts", customer_id=customer_id, count=len(accounts))

        # Convert to response schema
        from app.accounts.accounts_schemas import AccountListItem
        account_items = [AccountListItem.model_validate(acc) for acc in accounts]

        return AccountListResponse(accounts=account_items)

    def get_account_overview(
        self,
        account_id: int,
        customer_id: int,
        user: AppUser
    ) -> AccountOverviewResponse:
        """
        Get detailed overview for a specific account.

        Args:
            account_id: Account ID
            customer_id: Customer ID
            user: Authenticated user (for ownership verification)

        Returns:
            Detailed account overview with freshness information

        Raises:
            HTTPException: 403 if account doesn't belong to user's customer
            NotFoundError: If account not found (after ownership check)
        """
        # Verify ownership first - this raises HTTPException(403) if unauthorized
        verify_account_ownership(account_id, user, self.db)

        # Get account (we know it exists and belongs to the customer now)
        account = self.repo.get_account_by_id(account_id)
        if not account:
            # This shouldn't happen after verify_account_ownership, but defensive check
            raise NotFoundError(message=f"Account {account_id} not found")

        # Verify ownership (redundant check kept for backward compatibility)
        if account.customer_id != customer_id:
            logger.warning(
                "Unauthorized account access attempt",
                account_id=account_id,
                customer_id=customer_id,
                owner_id=account.customer_id
            )
            raise AuthorizationError(message="You do not have access to this account")

        # Get associated cards
        cards = self.repo.get_account_cards(account_id)
        card_details = [
            CreditCardDetail(
                id=card.id,
                card_number_masked=card.card_number_masked,
                card_type=card.card_type,
                card_status=card.card_status,
                expiry_month=card.expiry_month,
                expiry_year=card.expiry_year
            )
            for card in cards
        ]

        # Get freshness information
        freshness = self.freshness_service.classify("account", account_id)
        as_of = self.freshness_service.get_as_of_timestamp("account", account_id)

        logger.info("Retrieved account overview", account_id=account_id, freshness=freshness)

        # Build response
        return AccountOverviewResponse(
            id=account.id,
            account_number_masked=account.account_number_masked,
            sort_code_masked=account.sort_code_masked,
            account_status=account.account_status,
            credit_limit=account.credit_limit,
            available_credit=account.available_credit,
            current_balance=account.current_balance,
            minimum_payment_due=account.minimum_payment_due,
            payment_due_date=account.payment_due_date,
            cards=card_details,
            freshness=freshness,
            as_of=as_of
        )

    def select_account(
        self,
        session_id: int,
        account_id: Optional[int],
        customer_id: int,
        user: AppUser
    ) -> AccountSelectionResponse:
        """
        Select an account for the current session context.

        Args:
            session_id: Current session ID
            account_id: Account ID to select (or None to clear)
            customer_id: Customer ID
            user: Authenticated user (for ownership verification)

        Returns:
            Account selection response

        Raises:
            HTTPException: 403 if account doesn't belong to user's customer
            NotFoundError: If account or session not found
        """
        # If account_id is provided, verify ownership first
        if account_id is not None:
            # This raises HTTPException(403) if unauthorized
            verify_account_ownership(account_id, user, self.db)

            # Get account (we know it exists and belongs to the customer now)
            account = self.repo.get_account_by_id(account_id)
            if not account:
                # This shouldn't happen after verify_account_ownership, but defensive check
                raise NotFoundError(message=f"Account {account_id} not found")

            # Verify ownership (redundant check kept for backward compatibility)
            if account.customer_id != customer_id:
                logger.warning(
                    "Unauthorized account selection attempt",
                    account_id=account_id,
                    customer_id=customer_id,
                    owner_id=account.customer_id
                )
                raise AuthorizationError(message="You do not have access to this account")

        # Update session with selected account
        success = self.auth_repo.update_selected_account(session_id, account_id)

        if not success:
            raise NotFoundError(message="Session not found")

        message = "Account selected successfully" if account_id else "Account selection cleared"
        logger.info("Account selection updated", session_id=session_id, account_id=account_id)

        return AccountSelectionResponse(
            success=True,
            selected_account_id=account_id,
            message=message
        )

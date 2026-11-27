"""
Authentication middleware for session resolution.

## Ownership Verification

All account-scoped routes MUST verify that the requested account belongs to the
authenticated user's customer before processing the request. This prevents
unauthorized cross-customer data access.

### Usage Pattern

Every service that handles account-scoped requests must call `verify_account_ownership()`
before processing:

```python
from app.middleware.auth import verify_account_ownership

def get_account_data(account_id: int, user: AppUser, db: Session):
    # First, verify ownership
    verify_account_ownership(account_id, user, db)

    # Then proceed with business logic
    return process_account_data(account_id)
```

### Services Requiring Ownership Verification

The following domain services handle account-scoped operations and MUST implement
ownership verification on all account-scoped endpoints:

- **accounts** (AccountOverviewService) - ✓ IMPLEMENTED
- **balance_breakdowns** (BalanceBreakdownsService) - TODO
- **transactions** (TransactionsService) - TODO
- **payments** (PaymentsService) - TODO
- **direct_debits** (DirectDebitsService) - TODO
- **balance_transfers** (BalanceTransfersService) - TODO
- **money_transfers** (MoneyTransfersService) - TODO
- **status_tracker** (StatusTrackerService) - TODO

### Current Limitations

**IMPORTANT**: The current implementation uses a STUB_CUSTOMER_ID pattern because
the AppUser model does not yet have a customer_id foreign key relationship. This
means all users are treated as belonging to customer_id=1.

**Before production deployment**, the following schema migration is required:

1. Add `customer_id` column to `app_users` table with foreign key to `customers.id`
2. Update user registration/provisioning to assign proper customer_id
3. Update `verify_account_ownership()` to use `user.customer_id` instead of STUB_CUSTOMER_ID
4. Add database constraint to enforce the foreign key relationship

Until this migration is complete, the ownership check provides structural correctness
but limited security value in multi-tenant scenarios.
"""
from datetime import datetime, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AuthenticationError
from app.core.settings import settings
from app.models.app_user import AppUser
from app.models.credit_card_account import CreditCardAccount
from app.models.user_session import UserSession

security = HTTPBearer(auto_error=False)

# TODO: Remove this stub once AppUser has customer_id foreign key
# This is a temporary workaround to demonstrate the ownership verification pattern
STUB_CUSTOMER_ID = 1


def get_current_user_session(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> tuple[AppUser, UserSession]:
    """
    Resolve current user and session from JWT token.

    Args:
        request: HTTP request
        credentials: Bearer token credentials
        db: Database session

    Returns:
        Tuple of (user, session)

    Raises:
        AuthenticationError: If authentication fails
    """
    if not credentials:
        raise AuthenticationError(message="Missing authentication token")

    token = credentials.credentials

    try:
        # Decode JWT
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id_str = payload.get("sub")
        session_id_str = payload.get("session_id")

        if not user_id_str or not session_id_str:
            raise AuthenticationError(message="Invalid token payload")

        user_id: int = int(user_id_str)
        session_id: int = int(session_id_str)



    except jwt.ExpiredSignatureError:
        raise AuthenticationError(message="Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError(message="Invalid token")
    except (ValueError, TypeError):
        raise AuthenticationError(message="Invalid token format")

    # Fetch user
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not user:
        raise AuthenticationError(message="User not found")

    if not user.is_active:
        raise AuthenticationError(message="User account is inactive")

    # Fetch session
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == user_id
    ).first()

    if not session:
        raise AuthenticationError(message="Session not found")

    # Check if session is revoked
    if session.revoked_at is not None:
        raise AuthenticationError(message="Session has been revoked")

    # Check if session is expired
    now = datetime.now(timezone.utc)
    # Handle both timezone-aware and naive datetimes
    session_expires = session.expires_at
    if session_expires.tzinfo is None:
        session_expires = session_expires.replace(tzinfo=timezone.utc)

    if session_expires < now:
        raise AuthenticationError(message="Session has expired")

    # Store in request state
    request.state.user = user
    request.state.session = session

    return user, session


def get_current_user(
    user_session: tuple[AppUser, UserSession] = Depends(get_current_user_session)
) -> AppUser:
    """
    Extract current user from resolved session.

    Args:
        user_session: Tuple of (user, session) from get_current_user_session

    Returns:
        Current authenticated user
    """
    return user_session[0]


def require_step_up(
    user_session: tuple[AppUser, UserSession] = Depends(get_current_user_session)
) -> tuple[AppUser, UserSession]:
    """
    Require step-up authentication for high-risk operations.

    Args:
        user_session: Tuple of (user, session)

    Returns:
        Tuple of (user, session)

    Raises:
        HTTPException: If step-up is required but not present
    """
    user, session = user_session

    if session.step_up_verified_at is None:
        raise HTTPException(
            status_code=403,
            detail="Step-up authentication required for this operation"
        )

    # Check if step-up is still valid (5 minutes = 300 seconds)
    now = datetime.now(timezone.utc)
    step_up_verified = session.step_up_verified_at
    if step_up_verified.tzinfo is None:
        step_up_verified = step_up_verified.replace(tzinfo=timezone.utc)

    step_up_age = (now - step_up_verified).total_seconds()

    if step_up_age > 300:
        raise HTTPException(
            status_code=403,
            detail="Step-up authentication has expired. Please re-authenticate."
        )

    return user, session


def is_support_user(user: AppUser) -> bool:
    """
    Check if user has support role.

    Args:
        user: User to check

    Returns:
        True if user has support role
    """
    # Support users are identified by email starting with "support"
    # In production, this would check a role field or role mapping table
    return user.email.startswith("support")


def verify_account_ownership(account_id: int, user: AppUser, db: Session) -> None:
    """
    Verify that the requested account belongs to the authenticated user's customer.

    This function ensures that users can only access accounts owned by their
    customer, preventing unauthorized cross-customer data access.

    Args:
        account_id: The account ID being accessed
        user: The authenticated user making the request
        db: Database session

    Raises:
        HTTPException: 403 Forbidden if the account doesn't belong to the user's customer

    Example:
        ```python
        @router.get("/accounts/{account_id}/balance")
        def get_balance(
            account_id: int,
            user: AppUser = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            # Verify ownership before processing
            verify_account_ownership(account_id, user, db)

            # Proceed with business logic
            return calculate_balance(account_id, db)
        ```

    Note:
        This implementation currently uses STUB_CUSTOMER_ID because AppUser
        does not yet have a customer_id foreign key. Once the schema is migrated
        to add user.customer_id, this function should be updated to:

        ```python
        customer_id = user.customer_id
        ```

        instead of using the stub.
    """
    # TODO: Replace with user.customer_id once AppUser schema is updated
    # Currently all users are treated as customer_id=1 for demonstration
    customer_id = STUB_CUSTOMER_ID

    # Query the account and verify it belongs to the customer
    account = db.query(CreditCardAccount).filter(
        CreditCardAccount.id == account_id
    ).first()

    if not account:
        # Return 403 instead of 404 to avoid leaking information about
        # which account IDs exist in the system
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this account"
        )

    if account.customer_id != customer_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this account"
        )

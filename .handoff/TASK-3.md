# TASK-3: Backend Feature B1 - Account Overview and Multi-Account Context

## Implementation Summary

This task implements the authentication and account overview functionality for the CCIP Balance Breakdown Service backend.

## Mounted Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/login
Authenticate user and create session.

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "is_active": true,
    "is_superuser": true,
    "session_id": 1,
    "session_expires_at": "2026-11-26T12:30:00Z",
    "step_up_verified_at": null,
    "selected_account_id": null
  }
}
```

**Errors:**
- 401: Invalid credentials or inactive user
- 422: Validation error (invalid email format or password too short)
- 429: Rate limit exceeded (5 attempts per 15 minutes)

#### POST /api/v1/auth/logout
Logout user by revoking current session.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Errors:**
- 401: Missing or invalid authentication token
- 404: Session not found

#### DELETE /api/v1/auth/sessions/{session_id}
Revoke a specific session.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Session revoked successfully"
}
```

**Errors:**
- 401: Missing or invalid authentication token, or session belongs to another user
- 404: Session not found

#### POST /api/v1/auth/step-up
Perform step-up authentication for high-risk operations.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Step-up authentication successful",
  "valid_until": "2026-11-26T12:05:00Z"
}
```

**Errors:**
- 401: Invalid credentials
- 422: Validation error

**Notes:**
- Step-up is valid for 300 seconds (5 minutes)
- After expiry, step-up must be performed again for high-risk operations

#### GET /api/v1/auth/me
Get current user information and session details.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 1,
  "email": "admin@example.com",
  "is_active": true,
  "is_superuser": true,
  "session_id": 1,
  "session_expires_at": "2026-11-26T12:30:00Z",
  "step_up_verified_at": null,
  "selected_account_id": null
}
```

**Errors:**
- 401: Missing or invalid authentication token

### Account Endpoints

#### GET /api/v1/accounts
List all accounts for the current customer.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "accounts": [
    {
      "id": 1,
      "account_number_masked": "****1001",
      "account_status": "Active",
      "current_balance": "1799.50",
      "available_credit": "3200.50",
      "credit_limit": "5000.00"
    },
    {
      "id": 2,
      "account_number_masked": "****1002",
      "account_status": "Active",
      "current_balance": "2150.00",
      "available_credit": "7850.00",
      "credit_limit": "10000.00"
    }
  ]
}
```

**Errors:**
- 401: Missing or invalid authentication token

#### GET /api/v1/accounts/{id}/overview
Get detailed overview for a specific account.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 1,
  "account_number_masked": "****1001",
  "sort_code_masked": "12-34-56",
  "account_status": "Active",
  "credit_limit": "5000.00",
  "available_credit": "3200.50",
  "current_balance": "1799.50",
  "minimum_payment_due": "89.98",
  "payment_due_date": "2026-12-11T00:00:00Z",
  "cards": [
    {
      "id": 1,
      "card_number_masked": "****-****-****-1001",
      "card_type": "Visa",
      "card_status": "Active",
      "expiry_month": 12,
      "expiry_year": 2026
    }
  ],
  "freshness": "Current",
  "as_of": "2026-11-26T12:00:00Z"
}
```

**Errors:**
- 401: Missing or invalid authentication token
- 403: Account doesn't belong to current customer
- 404: Account not found

#### PUT /api/v1/accounts/selection
Select an account for the current session context.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "account_id": 1
}
```

**Response (200):**
```json
{
  "success": true,
  "selected_account_id": 1,
  "message": "Account selected successfully"
}
```

**To clear selection:**
```json
{
  "account_id": null
}
```

**Errors:**
- 401: Missing or invalid authentication token
- 403: Account doesn't belong to current customer
- 404: Account or session not found

## Seed Credentials

**Admin User:**
- Email: `admin@example.com`
- Password: `admin123`

## Seed Accounts

Three demo accounts are seeded for customer CUST-001:

1. **ACC-1001** (****1001)
   - Credit Limit: £5,000.00
   - Current Balance: £1,799.50
   - Available Credit: £3,200.50
   - Minimum Payment: £89.98
   - Payment Due: 15 days from seed date

2. **ACC-1002** (****1002)
   - Credit Limit: £10,000.00
   - Current Balance: £2,150.00
   - Available Credit: £7,850.00
   - Minimum Payment: £107.50
   - Payment Due: 20 days from seed date

3. **ACC-1003** (****1003)
   - Credit Limit: £3,000.00
   - Current Balance: £500.00
   - Available Credit: £2,500.00
   - Minimum Payment: £25.00
   - Payment Due: 10 days from seed date

## Backend Flows

### Login Flow

1. User submits credentials to POST /api/v1/auth/login
2. Rate limiter checks attempt count (5 per 15 minutes)
3. User is retrieved from database by email
4. Password is verified using bcrypt (cost factor 12)
5. User active status is checked
6. Session timeout is determined (900s for superuser, 1800s for regular user)
7. Session is created with hashed token and expiry
8. JWT is generated with user_id and session_id
9. JWT and user information are returned
10. Rate limiter is reset on successful login

### Logout/Revocation Flow

1. User calls POST /api/v1/auth/logout or DELETE /api/v1/auth/sessions/{session_id}
2. JWT token is validated via middleware
3. Session is retrieved from database
4. `revoked_at` timestamp is set to current UTC time
5. Database is committed
6. Success response is returned
7. Subsequent requests with same token will fail with 401
8. **Note:** There is a 1-minute propagation window where revoked sessions may still be accepted due to in-memory caching

### Get Current User Flow

1. User calls GET /api/v1/auth/me
2. JWT token is validated via middleware
3. User and session are retrieved from database
4. Session expiry and revocation status are checked
5. User information with session details is returned

### Step-Up Flow

1. User calls POST /api/v1/auth/step-up with password
2. JWT token is validated via middleware
3. Password is verified against user's hashed password
4. `step_up_verified_at` timestamp is set to current UTC time on session
5. Valid_until timestamp is calculated (current time + 300 seconds)
6. Session is updated and committed
7. Session moves to high-risk context for 5 minutes
8. After 300 seconds, step-up must be performed again for high-risk operations

### Account Selection Flow

1. User calls PUT /api/v1/accounts/selection with account_id
2. JWT token is validated via middleware
3. If account_id is provided:
   - Account is retrieved from database
   - Ownership is verified (account.customer_id == current customer)
   - If verification fails, 403 is returned
4. Session's `selected_account_id` is updated
5. Database is committed
6. Success response with selected_account_id is returned
7. Subsequent calls to GET /api/v1/auth/me will include selected_account_id

## Security Implementation

### Password Hashing
- Uses bcrypt with cost factor 12
- Passwords are never stored in plaintext
- Password verification uses constant-time comparison

### JWT Tokens
- Algorithm: HS256
- Expiry: Included in payload (exp claim)
- Payload includes: user_id (sub), session_id, issued_at (iat)
- Secret key configurable via JWT_SECRET_KEY environment variable

### Rate Limiting
- Login endpoint: 5 attempts per 15 minutes per email
- Counter stored in-memory (resets on application restart)
- Can be disabled via RATE_LIMIT_ENABLED=false for testing

### Session Management
- Server-side session records in user_sessions table
- Sessions can be revoked individually
- Expired sessions are rejected
- Revoked sessions are rejected (1-minute propagation window)

### Logging
- Structured logging with structlog
- PII masking for emails and sensitive fields
- Correlation ID attached to all requests
- Security events logged (failed login, unauthorized access attempts)

### Middleware
- CorrelationIDMiddleware: Adds X-Correlation-ID to requests
- Authentication middleware: Validates JWT and resolves user/session
- Error handlers: Centralized error handling with proper status codes

## Testing

All tests are located in:
- `/repos/ccip-balance-breakdown-service/backend/tests/test_auth/`
- `/repos/ccip-balance-breakdown-service/backend/tests/test_accounts/`

Run tests with:
```bash
cd /repos/ccip-balance-breakdown-service/backend
.venv/bin/python -m pytest tests/test_auth/ -v
.venv/bin/python -m pytest tests/test_accounts/ -v
```

## Dependencies Added

- structlog>=24.4.0 (structured logging)
- email-validator>=2.2.0 (email validation in Pydantic)

## Notes

- Customer association is currently stubbed (STUB_CUSTOMER_ID = 1)
- Real implementation would derive customer from authenticated user
- Freshness service is stubbed (always returns "Current")
- Real implementation would check synchronization_records table

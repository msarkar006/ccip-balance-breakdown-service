# TASK-6 Handoff: Payment Initiation and Direct Debit Coverage

## Mounted Endpoints

### Payment Endpoints
- **POST /api/v1/payments** - Initiate one-off or scheduled payment
  - Requires `Idempotency-Key` header
  - Requires `X-Step-Up-Proof` header (step-up scope: `payment`)
  - Request body: `PaymentInitiationRequest` with account_id, amount (must be > 0 and ≤ current balance), currency, payment_method, optional scheduled_date, idempotency_key
  - Response: 201 with `PaymentInitiationResponse` containing payment details, status (Submitted/Restricted), and optional guidance
  - Executes HighRiskWritePipeline: ownership → step-up → schema → idempotency → business rules → risk decision → rail submission → atomic commit + tracking event → publish event + audit

- **GET /api/v1/payments/guidance** - Get payment guidance with balance and direct debit coverage
  - Query parameter: `account_id` (required)
  - Response: `PaymentGuidanceResponse` with minimum_payment, due_date, current_balance, max_payment_amount, and embedded `DirectDebitCoverageResponse`
  - Calls `DirectDebitService.derive_coverage` to assess whether active direct debit is expected to cover minimum payment

### Direct Debit Endpoints
- **GET /api/v1/direct-debits** - List all mandates for an account
  - Query parameter: `account_id` (required)
  - Response: `DirectDebitListResponse` with list of mandates (id, mandate_reference, mandate_type, payment_amount, status, activated_at, created_at)
  - Ordered by created_at DESC

- **POST /api/v1/direct-debits/change-requests** - Initiate mandate change
  - Requires `Idempotency-Key` header
  - Requires `X-Step-Up-Proof` header (step-up scope: `direct_debit_change`)
  - Request body: `ChangeRequestRequest` with mandate_id, change_type (Amend/Cancel/Reinstate), optional new_payment_amount (required for Amend), idempotency_key
  - Response: 201 with `ChangeRequestResponse` containing change request details
  - Executes HighRiskWritePipeline: ownership → step-up → schema → idempotency → business rules → risk decision → rail submission → atomic commit → publish event + audit

## Request/Response Shapes

### POST /api/v1/payments
Request:
```json
{
  "account_id": 1,
  "amount": "100.00",
  "currency": "GBP",
  "payment_method": "BankTransfer",
  "scheduled_date": null,
  "idempotency_key": "unique-client-key-123"
}
```

Response (201):
```json
{
  "id": 1,
  "account_id": 1,
  "external_payment_id": "EXT-PMT-ABC123",
  "idempotency_key": "unique-client-key-123",
  "amount": "100.00",
  "currency": "GBP",
  "status": "Submitted",
  "scheduled_date": null,
  "created_at": "2026-11-26T10:00:00Z",
  "guidance": null
}
```

Response (Restricted):
```json
{
  ...
  "status": "Restricted",
  "guidance": {
    "message_code": "payment_restricted",
    "message": "This payment requires additional review.",
    "next_step": "Our team will contact you if needed"
  }
}
```

### GET /api/v1/payments/guidance
Response:
```json
{
  "minimum_payment": "89.98",
  "due_date": "2026-12-15T00:00:00Z",
  "current_balance": "1799.50",
  "max_payment_amount": "1799.50",
  "direct_debit_coverage": {
    "coverage_status": "expected_to_cover",
    "manual_payment_may_be_required": false,
    "reason": "Active MinimumPayment mandate with recent collection"
  }
}
```

DirectDebitCoverage statuses:
- `expected_to_cover`: Active mandate with sufficient amount/type
- `not_expected_to_cover`: Active mandate but insufficient amount
- `cannot_be_confirmed`: No active mandate or missing/stale data

### GET /api/v1/direct-debits
Response:
```json
{
  "mandates": [
    {
      "id": 1,
      "mandate_reference": "DD-1001-MIN",
      "mandate_type": "MinimumPayment",
      "payment_amount": null,
      "status": "Active",
      "activated_at": "2026-10-01T00:00:00Z",
      "created_at": "2026-10-01T00:00:00Z"
    }
  ]
}
```

### POST /api/v1/direct-debits/change-requests
Request:
```json
{
  "mandate_id": 1,
  "change_type": "Amend",
  "new_payment_amount": "120.00",
  "idempotency_key": "unique-client-key-456"
}
```

Response (201):
```json
{
  "id": 1,
  "mandate_id": 1,
  "change_type": "Amend",
  "new_payment_amount": "120.00",
  "status": "Submitted",
  "created_at": "2026-11-26T10:00:00Z"
}
```

## Seed Mandates

Demo direct debit mandates seeded:
- **ACC-1001** (****1001): Active MinimumPayment mandate (DD-1001-MIN) - activated 60 days ago, payment_amount null
- **ACC-1002** (****1002): Pending StatementBalance mandate (DD-1002-STMT) - not yet activated, payment_amount null
- **ACC-1003** (****1003): Cancelled FixedAmount mandate (DD-1003-FIXED) - activated 90 days ago, payment_amount £50.00

## Seed Payments

Demo payments from TASK-5 (PMT-1 to PMT-7) are now writable via POST /api/v1/payments.
Latest payment for ACC-1001: PMT-6 (DirectDebit, Completed, £89.98) - demonstrates recent direct debit collection for coverage derivation.

## Seed Audit Events

Demo audit events seeded:
- Login event (user 1, access_2y retention, 1 day ago)
- Logout event (user 1, access_2y retention, 12 hours ago)
- Step-up event (user 1, access_2y retention, scope: payment, 6 hours ago)

## Backend Flows

### Payment Initiation Flow (POST /api/v1/payments)
1. Router extracts user and session via `require_step_up` dependency (enforces step-up auth)
2. PaymentService.initiate_payment builds PaymentInitiationPipeline
3. Pipeline executes HighRiskWritePipeline steps:
   - Ownership check: verifies account exists (stub ownership)
   - Step-up verification: checks step_up_verified flag (403 if false)
   - Schema validation: amount > 0
   - Idempotency lookup: checks (account_id, idempotency_key), returns existing if found
   - Business rules: amount ≤ current_balance (422 if exceeded)
   - Risk decision: calls StubFraudAndRiskAdapter.assess_payment (allow=True stub)
   - Source submission: calls StubPaymentRailAdapter.submit_payment (returns mock external ID)
   - Atomic commit: creates Payment with status Submitted (or Restricted if risk denies), creates first TrackingEvent, commits transaction
   - Publish event: stub (would publish servicing.payment.submitted in production)
   - Audit: writes AuditLog with action=payment_initiation, entity_type=payment, retention_class=financial_7y
4. Returns 201 with PaymentInitiationResponse

### Payment Guidance Flow (GET /api/v1/payments/guidance)
1. Router extracts account_id from query
2. PaymentService.get_payment_guidance fetches CreditCardAccount
3. Calls DirectDebitService.derive_coverage(account_id, minimum_payment)
4. DirectDebitService logic:
   - Fetches active mandate for account
   - If no mandate: returns cannot_be_confirmed
   - If MinimumPayment: checks for recent (35 days) DirectDebit payment → expected_to_cover if recent, cannot_be_confirmed if stale
   - If StatementBalance: returns expected_to_cover (always covers)
   - If FixedAmount: compares payment_amount vs minimum_payment → expected_to_cover if sufficient, not_expected_to_cover if insufficient, cannot_be_confirmed if data missing
5. Returns PaymentGuidanceResponse with balance info and coverage assessment

### Direct Debit Change Flow (POST /api/v1/direct-debits/change-requests)
1. Router extracts user and session via `require_step_up` dependency (enforces step-up auth)
2. DirectDebitService.initiate_change builds DirectDebitChangePipeline
3. Pipeline executes HighRiskWritePipeline steps:
   - Ownership check: verifies account exists and mandate belongs to account
   - Step-up verification: checks step_up_verified flag (403 if false)
   - Schema validation: change_type in [Amend, Cancel, Reinstate], new_payment_amount required for Amend
   - Idempotency lookup: checks (mandate_id, idempotency_key), returns existing if found
   - Business rules: mandate exists and belongs to account
   - Risk decision: calls StubFraudAndRiskAdapter.assess_direct_debit_change (allow=True stub)
   - Source submission: calls StubDirectDebitRailAdapter.submit_change_request (returns mock external ID)
   - Atomic commit: creates DirectDebitChangeRequest with status Submitted (or Restricted if risk denies), commits transaction
   - Publish event: stub (would publish in production)
   - Audit: writes AuditLog with action=direct_debit_change, entity_type=direct_debit_change_request, retention_class=financial_7y
4. Returns 201 with ChangeRequestResponse

## Implementation Notes

### HighRiskWritePipeline
- Core template method class at `app/core/pipeline.py`
- Enforces fixed pipeline order: ownership → step-up → schema → idempotency → business rules → risk decision → source submission → atomic commit + tracking event → publish event + audit
- Subclasses implement each step as abstract methods
- Used by PaymentInitiationPipeline and DirectDebitChangePipeline

### Adapters
All adapters have stub implementations that allow operations and return mock external IDs:
- `IdentityStepUpAdapter`: verify_step_up (always returns verified=True)
- `PaymentRailAdapter`: submit_payment (returns EXT-PMT-{random})
- `DirectDebitRailAdapter`: submit_change_request (returns EXT-DDC-{random})
- `FraudAndRiskAdapter`: assess_payment and assess_direct_debit_change (always returns allow=True)

### AuditService
- Retention classes: financial_7y (financial audit), access_2y (access control), tracking_24m (tracking)
- record() method captures user_id, action, entity_type, entity_id, severity, correlation_id, details, ip_address
- Writes to audit_logs table with occurred_at timestamp

### DirectDebitService Coverage Derivation
Logic rules:
- MinimumPayment: expected_to_cover if recent (35 days) DirectDebit payment exists, cannot_be_confirmed otherwise
- StatementBalance: always expected_to_cover
- FixedAmount: compares payment_amount vs minimum_payment threshold
- No active mandate: cannot_be_confirmed
- manual_payment_may_be_required flag set for not_expected_to_cover and cannot_be_confirmed states

### Step-Up Requirement
Both POST endpoints require step-up authentication:
- middleware/auth.py provides require_step_up dependency
- Checks session.step_up_verified_at is not None and within 300 seconds (5 minutes)
- Returns 403 if step-up missing or expired
- Task scope specifies step-up scope 'payment' for payments and 'direct_debit_change' for direct debits (not enforced in stub)

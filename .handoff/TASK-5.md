# TASK-5 Handoff: Backend Feature B3 - Transactions and Payment History

## Mounted Endpoints

### Transaction Endpoints
- `GET /api/v1/transactions` - Paginated transaction history
  - Full path: `GET /api/v1/transactions` (router prefix includes `/api/v1`)
  - Query parameters:
    - `account_id` (required): Account ID to filter transactions
    - `limit` (optional, default 25, range 1-100): Maximum items to return
    - `offset` (optional, default 0): Number of items to skip
  - Returns: `TransactionListResponse` with page envelope

### Payment Endpoints
- `GET /api/v1/payments` - Paginated payment history
  - Full path: `GET /api/v1/payments` (router prefix includes `/api/v1`)
  - Query parameters:
    - `account_id` (required): Account ID to filter payments
    - `payment_type` (optional): Payment type filter (Scheduled, OneOff, DirectDebitCollection)
    - `limit` (optional, default 25, range 1-100): Maximum items to return
    - `offset` (optional, default 0): Number of items to skip
  - Returns: `PaymentListResponse` with page envelope

- `GET /api/v1/payments/{id}` - Payment detail with timeline
  - Full path: `GET /api/v1/payments/{id}` (router prefix includes `/api/v1`)
  - Path parameter:
    - `id` (required): Payment ID
  - Returns: `PaymentDetailResponse` with payment resource, timeline, can_cancel flag, cancellation_message, and guidance

## Request/Response Shapes

### Transaction List Response
```json
{
  "items": [
    {
      "id": 1,
      "account_id": 123,
      "external_transaction_id": "TXN-001",
      "transaction_date": "2026-11-21T14:30:00Z",
      "posting_date": "2026-11-23T10:00:00Z",
      "merchant_name": "Grocery Store",
      "transaction_type": "Purchase",
      "amount": "45.67",
      "currency": "GBP",
      "status": "Posted",
      "description": "Weekly groceries",
      "created_at": "2026-11-21T14:30:00Z",
      "updated_at": "2026-11-23T10:00:00Z"
    }
  ],
  "total": 20,
  "limit": 25,
  "offset": 0,
  "has_more": false,
  "empty_state_message": null,
  "freshness": {
    "level": "Current",
    "as_of": null
  }
}
```

### Payment List Response
```json
{
  "items": [
    {
      "id": 1,
      "account_id": 123,
      "external_payment_id": "PMT-1",
      "idempotency_key": null,
      "payment_method": "BankTransfer",
      "amount": "100.00",
      "currency": "GBP",
      "status": "Completed",
      "scheduled_date": null,
      "processed_at": "2026-11-16T10:00:00Z",
      "created_at": "2026-11-15T14:00:00Z",
      "updated_at": "2026-11-16T10:00:00Z"
    }
  ],
  "total": 7,
  "limit": 25,
  "offset": 0,
  "has_more": false,
  "empty_state_message": null,
  "freshness": {
    "level": "Current",
    "as_of": null
  }
}
```

### Payment Detail Response
```json
{
  "payment": {
    "id": 1,
    "account_id": 123,
    "external_payment_id": "PMT-1",
    "idempotency_key": null,
    "payment_method": "BankTransfer",
    "amount": "100.00",
    "currency": "GBP",
    "status": "Completed",
    "scheduled_date": null,
    "processed_at": "2026-11-16T10:00:00Z",
    "created_at": "2026-11-15T14:00:00Z",
    "updated_at": "2026-11-16T10:00:00Z"
  },
  "timeline": [
    {
      "event_type": "submitted",
      "status": "Submitted",
      "event_timestamp": "2026-11-15T14:00:00Z",
      "description": "Payment PMT-1 submitted"
    },
    {
      "event_type": "processing",
      "status": "Processing",
      "event_timestamp": "2026-11-15T22:00:00Z",
      "description": "Payment PMT-1 processing"
    },
    {
      "event_type": "completed",
      "status": "Completed",
      "event_timestamp": "2026-11-16T10:00:00Z",
      "description": "Payment PMT-1 completed"
    }
  ],
  "can_cancel": false,
  "cancellation_message": "Payment already completed",
  "guidance": null
}
```

### TrackerMilestone
```json
{
  "event_type": "submitted",
  "status": "Submitted",
  "event_timestamp": "2026-11-15T14:00:00Z",
  "description": "Payment submitted"
}
```

## Seed Data

### Transaction IDs (account ACC-1001)
- 20 transactions total:
  - 14 Posted transactions (TXN-001 to TXN-014) with posting_date populated
  - 6 Pending transactions (TXN-015 to TXN-020) with posting_date = null
- Transactions ordered by transaction_date DESC
- Status values: "Posted", "Pending"
- Merchant names vary, amounts range from £4.50 to £156.00

### Payment IDs (account ACC-1001)
- PMT-1: Completed OneOff, £100.00, BankTransfer, processed 10 days ago
- PMT-2: Processing Scheduled, £150.00, BankTransfer, scheduled in 5 days
- PMT-3: Failed OneOff, £200.00, DebitCard, failed 3 days ago
- PMT-4: Submitted Scheduled, £250.00, BankTransfer, scheduled in 10 days
- PMT-5: Cancelled Scheduled, £180.00, BankTransfer, scheduled in 15 days
- PMT-6: Completed DirectDebitCollection, £89.98, DirectDebit, processed 5 days ago
- PMT-7: Restricted Scheduled, £500.00, BankTransfer, scheduled in 20 days

Each payment has associated tracking events in the tracking_events table.

## Backend Flows

### Transaction Query Flow
1. TransactionService receives account_id, limit, offset parameters
2. TransactionsRepository queries transactions table filtered by account_id
3. Transactions ordered by transaction_date DESC
4. Total count computed separately for pagination
5. Response includes:
   - items: list of transactions with Pending/Posted status
   - total: total count for account
   - limit, offset: pagination parameters
   - has_more: computed as (offset + limit) < total
   - empty_state_message: set when total = 0
   - freshness: stub returning {"level": "Current", "as_of": null}

### Payment History Flow
1. PaymentService receives account_id, payment_type (optional), limit, offset
2. PaymentsRepository queries payments table filtered by account_id
3. Payments ordered by scheduled_date DESC NULLS LAST, then created_at DESC
4. Total count computed separately for pagination
5. Response includes page envelope with same structure as transactions

### Payment Detail Flow
1. PaymentService receives payment_id
2. PaymentsRepository retrieves payment by ID (raises NotFoundError if missing)
3. PaymentsRepository retrieves tracking_events for entity_type="Payment", entity_id=payment_id
4. Timeline built from tracking events ordered by occurred_at ASC
5. can_cancel computed based on:
   - Only Submitted or Processing payments can be cancelled
   - Scheduled payments: can cancel if scheduled_date is in the future
   - Immediate payments: can cancel only if status is Submitted
6. cancellation_message provides explanation when can_cancel is false
7. guidance object returned for Processing, Failed, or Restricted payments
8. Response includes payment resource, timeline, can_cancel, cancellation_message, guidance

### Status Tracking Stub
- StatusTrackingService provides two stub methods:
  - `record_event`: writes tracking_events rows
  - `get_tracker_view`: returns empty list (full implementation deferred)
- Tracking events are written at payment lifecycle milestones
- Events stored with entity_type="Payment", entity_id=str(payment.id), occurred_at timestamp

## Testing Coverage

### Transaction Tests (8 tests in test_transactions.py)
- `test_get_transactions_success`: Basic retrieval with pagination envelope
- `test_get_transactions_pending_vs_posted`: Pending vs Posted distinction with posting_date
- `test_get_transactions_pagination`: Pagination with has_more flag
- `test_get_transactions_empty_state`: Empty state message when no transactions
- `test_get_transactions_requires_auth`: Authentication requirement

### Payment Tests (8 tests in test_payments.py)
- `test_get_payments_success`: Basic retrieval with pagination envelope
- `test_get_payment_detail_with_timeline`: Detail with tracking events timeline
- `test_payment_can_cancel_logic`: Cancellation availability logic
- `test_payment_guidance_messages`: Guidance for Processing, Failed, Restricted states
- `test_get_payments_empty_state`: Empty state message when no payments
- `test_get_payment_not_found`: 404 for non-existent payment
- `test_get_payments_requires_auth`: List endpoint requires authentication
- `test_get_payment_detail_requires_auth`: Detail endpoint requires authentication

## Module Structure

### Transactions Domain
- `app/transactions/__init__.py`
- `app/transactions/transactions_models.py` - re-exports Transaction model
- `app/transactions/transactions_schemas.py` - TransactionResponse, TransactionListResponse
- `app/transactions/transactions_repository.py` - TransactionsRepository with get_transactions_by_account
- `app/transactions/transactions_service.py` - TransactionService with get_transactions method
- `app/transactions/transactions.py` - FastAPI router with GET /api/v1/transactions endpoint

### Payments Domain
- `app/payments/__init__.py`
- `app/payments/payments_models.py` - re-exports Payment model
- `app/payments/payments_schemas.py` - PaymentResponse, PaymentDetailResponse, PaymentListResponse, TrackerMilestone
- `app/payments/payments_repository.py` - PaymentsRepository with get_payments_by_account, get_payment_by_id, get_tracking_events_for_payment
- `app/payments/payments_service.py` - PaymentService with get_payments and get_payment_detail methods
- `app/payments/payments.py` - FastAPI router with GET /api/v1/payments and GET /api/v1/payments/{id} endpoints

### Status Tracker Domain (stub)
- `app/status_tracker/__init__.py`
- `app/status_tracker/status_tracker_models.py` - re-exports TrackingEvent model
- `app/status_tracker/status_tracker_schemas.py` - TrackerItem, TrackerMilestone
- `app/status_tracker/status_tracker_service.py` - StatusTrackingService stub with record_event and get_tracker_view methods

## Router Registration
Both routers registered in `app/main.py`:
```python
app.include_router(transactions_router)
app.include_router(payments_router)
```

## Seed Data Updates
- Added 20 demo transactions for account ACC-1001 (14 Posted, 6 Pending)
- Added 7 demo payments for account ACC-1001 (PMT-1 to PMT-7)
- Each payment has associated tracking events demonstrating lifecycle progression
- Transactions demonstrate Pending vs Posted distinction with posting_date field
- Payments demonstrate different status values and scheduled vs immediate payments

## Dependencies
- Depends on TASK-3 for authentication, accounts, and database schema
- Uses existing Transaction, Payment, TrackingEvent models from TASK-1
- Uses existing FreshnessAndSyncService stub for freshness classification

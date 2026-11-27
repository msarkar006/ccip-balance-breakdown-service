# TASK-7 Handoff: Backend Feature B5 - Balance Transfer and Money Transfer Tracking

## Implementation Summary

Implemented read-only balance transfer and money transfer tracking with timeline, promotional context, source linkage, and guidance.

## Mounted Endpoints

### Balance Transfers
- `GET /api/v1/balance-transfers` - Paginated balance transfer history
  - Query params: `account_id` (required), `limit` (default 10), `offset` (default 0)
  - Returns: `BalanceTransferListResponse` with items, total, limit, offset, has_more
  - Ordered by: `requested_on DESC` (created_at DESC)

- `GET /api/v1/balance-transfers/{id}` - Balance transfer detail
  - Query params: `account_id` (required, ownership verification)
  - Returns: `BalanceTransferDetailResponse` with timeline, promotional context, source_link, guidance

### Money Transfers
- `GET /api/v1/money-transfers` - Paginated money transfer history
  - Query params: `account_id` (required), `limit` (default 10), `offset` (default 0)
  - Returns: `MoneyTransferListResponse` with items, total, limit, offset, has_more
  - Ordered by: `requested_on DESC` (created_at DESC)

- `GET /api/v1/money-transfers/{id}` - Money transfer detail
  - Query params: `account_id` (required, ownership verification)
  - Returns: `MoneyTransferDetailResponse` with payee, timeline, guidance

## Request/Response Shapes

### Balance Transfer List Response
```json
{
  "items": [
    {
      "id": 1,
      "external_transfer_id": "BT-1",
      "transfer_amount": "1000.00",
      "promotional_rate": "0.00",
      "status": "Submitted",
      "requested_on": "2026-11-26T10:00:00Z",
      "processed_at": null
    }
  ],
  "total": 7,
  "limit": 10,
  "offset": 0,
  "has_more": false
}
```

### Balance Transfer Detail Response
```json
{
  "id": 3,
  "account_id": 1,
  "external_transfer_id": "BT-3",
  "transfer_amount": "500.00",
  "status": "Completed",
  "requested_on": "2026-10-27T10:00:00Z",
  "processed_at": "2026-10-27T12:00:00Z",
  "timeline": [
    {
      "event_type": "submitted",
      "status": "Submitted",
      "occurred_at": "2026-10-25T10:00:00Z",
      "event_data": "Balance transfer BT-3 submitted"
    },
    {
      "event_type": "processing",
      "status": "Processing",
      "occurred_at": "2026-10-26T10:00:00Z",
      "event_data": "Balance transfer BT-3 processing"
    },
    {
      "event_type": "completed",
      "status": "Completed",
      "occurred_at": "2026-10-27T12:00:00Z",
      "event_data": "Balance transfer BT-3 completed"
    }
  ],
  "promotional_context": {
    "promo_rate": "0.00",
    "promo_start_date": "2026-10-27T12:00:00Z",
    "promo_end_date": "2027-10-27T12:00:00Z",
    "revert_rate": null
  },
  "source_link": {
    "source_type": "BalanceTransfer",
    "source_id": 3,
    "source_reference": "BT-3",
    "category_id": 5,
    "category_name": "BalanceTransfer"
  },
  "guidance": null,
  "created_at": "2026-10-27T10:00:00Z",
  "updated_at": "2026-10-27T12:00:00Z"
}
```

### TrackerMilestone Object
```json
{
  "event_type": "submitted",
  "status": "Submitted",
  "occurred_at": "2026-11-26T10:00:00Z",
  "event_data": "Transfer submitted"
}
```

### Promotional Context Object
```json
{
  "promo_rate": "0.00",
  "promo_start_date": "2026-10-27T12:00:00Z",
  "promo_end_date": "2027-10-27T12:00:00Z",
  "revert_rate": null
}
```

### Source Link Object (Balance Transfer)
```json
{
  "source_type": "BalanceTransfer",
  "source_id": 3,
  "source_reference": "BT-3",
  "category_id": 5,
  "category_name": "BalanceTransfer"
}
```

### Guidance Object
```json
{
  "message_code": "BT_REJECTED",
  "message": "This balance transfer was rejected. Please review the rejection reason and consider resubmitting with updated information.",
  "next_step": "Contact customer service for details or submit a new transfer request."
}
```

### Money Transfer List Response
```json
{
  "items": [
    {
      "id": 1,
      "external_transfer_id": "MT-1",
      "payee_name": "John Smith",
      "amount": "100.00",
      "currency": "GBP",
      "status": "Submitted",
      "requested_on": "2026-11-26T10:00:00Z",
      "processed_at": null
    }
  ],
  "total": 4,
  "limit": 10,
  "offset": 0,
  "has_more": false
}
```

### Money Transfer Detail Response
```json
{
  "id": 3,
  "account_id": 1,
  "external_transfer_id": "MT-3",
  "payee": {
    "payee_id": 1,
    "payee_name": "John Smith",
    "account_number_masked": "****1234",
    "sort_code_masked": "12-34-56"
  },
  "amount": "150.00",
  "currency": "GBP",
  "fee_context": null,
  "status": "Completed",
  "requested_on": "2026-11-23T10:00:00Z",
  "processed_at": "2026-11-23T12:00:00Z",
  "timeline": [
    {
      "event_type": "submitted",
      "status": "Submitted",
      "occurred_at": "2026-11-22T10:00:00Z",
      "event_data": "Money transfer MT-3 submitted"
    },
    {
      "event_type": "processing",
      "status": "Processing",
      "occurred_at": "2026-11-23T00:00:00Z",
      "event_data": "Money transfer MT-3 processing"
    },
    {
      "event_type": "completed",
      "status": "Completed",
      "occurred_at": "2026-11-23T12:00:00Z",
      "event_data": "Money transfer MT-3 completed"
    }
  ],
  "guidance": null,
  "created_at": "2026-11-23T10:00:00Z",
  "updated_at": "2026-11-23T12:00:00Z"
}
```

## Seed Balance Transfer IDs

Seed data includes 7 demo balance transfers for ACC-1001:
- **BT-1**: Submitted (no timeline events yet, just submitted)
- **BT-2**: ReviewRequired (submitted → review_required)
- **BT-3**: Completed with promo context (0% for 12 months, linked to BalanceTransfer category in ACC-1001 breakdown)
- **BT-4**: Completed with promo context (3.9% for 24 months)
- **BT-5**: Rejected with guidance (rejected status triggers guidance message)
- **BT-6**: Completed
- **BT-7**: Submitted

## Seed Money Transfer IDs

Seed data includes 4 demo money transfers for ACC-1001:
- **MT-1**: Submitted to John Smith (£100.00)
- **MT-2**: Processing to Jane Doe (£250.00)
- **MT-3**: Completed to John Smith (£150.00)
- **MT-4**: Blocked to ACME Corp (£500.00, triggers escalation guidance)

Seed also includes 3 payees:
- Payee 1: John Smith (****1234, 12-34-56)
- Payee 2: Jane Doe (****5678, 98-76-54)
- Payee 3: ACME Corp (****9012, 11-22-33)

## Backend Flows

### Balance Transfer Detail Flow
1. Query `BalanceTransfer` by ID with account_id ownership check
2. Query `TrackingEvent` for entity_type="BalanceTransfer" and entity_id, ordered by occurred_at ASC
3. Build promotional context if promotional_rate and promotional_period_months present:
   - `promo_start_date` = processed_at or created_at
   - `promo_end_date` = promo_start_date + (promotional_period_months * 30 days)
4. Query `BalanceCategory` with source_balance_transfer_id = transfer.id to find linked category
5. Build source_link if category found
6. Build guidance if status is "Rejected" or "ReviewRequired"
7. Return `BalanceTransferDetailResponse`

### Money Transfer Detail Flow
1. Query `MoneyTransfer` by ID with account_id ownership check
2. Query `Payee` by payee_id for payee details
3. Query `TrackingEvent` for entity_type="MoneyTransfer" and entity_id, ordered by occurred_at ASC
4. Build guidance if status is "Failed", "Rejected", "Delayed", or "Blocked"
5. Return `MoneyTransferDetailResponse`

### Guidance Rules

**Balance Transfer Guidance:**
- Status = "Rejected" → `BT_REJECTED` with resubmission guidance
- Status = "ReviewRequired" → `BT_REVIEW_REQUIRED` with wait guidance

**Money Transfer Guidance:**
- Status = "Failed" → `MT_FAILED` with retry guidance
- Status = "Rejected" → `MT_REJECTED` with correction guidance
- Status = "Delayed" → `MT_DELAYED` with wait guidance
- Status = "Blocked" → `MT_BLOCKED` with escalation guidance

## Module Structure

### Balance Transfers Domain
- `app/balance_transfers/__init__.py`
- `app/balance_transfers/balance_transfers_models.py` - Re-exports BalanceTransfer
- `app/balance_transfers/balance_transfers_schemas.py` - Request/response schemas
- `app/balance_transfers/balance_transfers_repository.py` - Data access layer
- `app/balance_transfers/balance_transfers_service.py` - Business logic
- `app/balance_transfers/balance_transfers.py` - FastAPI router

### Money Transfers Domain
- `app/money_transfers/__init__.py`
- `app/money_transfers/money_transfers_models.py` - Re-exports MoneyTransfer, Payee
- `app/money_transfers/money_transfers_schemas.py` - Request/response schemas
- `app/money_transfers/money_transfers_repository.py` - Data access layer
- `app/money_transfers/money_transfers_service.py` - Business logic
- `app/money_transfers/money_transfers.py` - FastAPI router

### Tests
- `tests/test_balance_transfers/test_balance_transfers.py` - 8 tests covering history, detail, timeline, promotional context, linked category, guidance, pagination, auth
- `tests/test_money_transfers/test_money_transfers.py` - 8 tests covering history, detail, timeline, payee info, guidance (failed/blocked), pagination, auth

## Key Dependencies

- Existing models: `BalanceTransfer`, `MoneyTransfer`, `Payee`, `TrackingEvent`, `BalanceCategory`
- StatusTrackingService: tracking event retrieval (read-only stub)
- Auth middleware: JWT authentication on all endpoints

## Notes

- Read-only tracking implementation (initiation deferred to TASK-8)
- Timeline built from tracking_events ordered by occurred_at ASC
- Promotional context computed from transfer fields (promotional_rate, promotional_period_months)
- Source linkage via balance_categories.source_balance_transfer_id foreign key
- Guidance triggered by specific status values (Rejected, ReviewRequired, Failed, Delayed, Blocked)
- All endpoints require authentication
- Pagination follows standard envelope: items, total, limit, offset, has_more

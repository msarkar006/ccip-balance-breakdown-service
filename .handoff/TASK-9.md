# TASK-9 Handoff: Instalment Plans and Unified Status Tracker

## Overview
Implemented FR-INS-001 (Instalment plan visibility and explanation) and FR-STA-001 (Unified status tracker, refresh, escalation and degradation messaging) with read-only instalment plan endpoints, unified tracker aggregation, on-demand refresh, and escalation guidance.

## Mounted Endpoints

### Instalment Plans
- **GET /api/v1/instalments**
  - Lists instalment plans filtered by account_id and instalment_status (defaults to "Active")
  - Ordered by created_at DESC (representing start_date in plan lifecycle)
  - Pagination with page envelope: items, total, limit, offset, has_more
  - Empty state message when no plans found

- **GET /api/v1/instalments/{plan_id}**
  - Returns detailed plan resource with obligation context
  - source_transaction: null (FR-INS-002 deferred - no conversion from transaction)
  - linked_category: Balance category when source_instalment_plan_id links plan to category
  - balance_effect object:
    - is_reflected_in_balance: true when linked category exists
    - explanation: Text explaining how plan affects total balance

### Status Tracker
- **GET /api/v1/status-tracker**
  - Aggregates TrackerItem from payments, money_transfers, balance_transfers, direct_debit_change_requests
  - Filters: account_id (required), status_group=unresolved (optional, filters to non-final states)
  - Returns: paginated items, total, unresolved_count, overall_message
  - overall_message: Escalation guidance when all sources unavailable or multiple items escalated

- **GET /api/v1/status-tracker/{entity_type}/{entity_id}**
  - Returns TrackerItem + milestones array (tracking events ordered by occurred_at ASC)
  - timeline_freshness: Freshness of timeline data
  - Supported entity types: Payment, MoneyTransfer, BalanceTransfer, DirectDebitChangeRequest

- **POST /api/v1/status-tracker/{entity_type}/{entity_id}/refresh**
  - Calls FreshnessAndSyncService.sync_one for on-demand sync
  - Throttled to once per entity per 10 seconds (429 if within window)
  - Returns: tracker_item, refresh_outcome (updated/unchanged/failed), refresh_message

## Request/Response Shapes

### InstalmentPlanListResponse
```json
{
  "items": [
    {
      "id": 1,
      "plan_reference": "IP-1",
      "plan_name": "IP-1 - 12 months",
      "original_amount": "1200.00",
      "remaining_balance": "800.00",
      "instalment_count": 12,
      "monthly_payment": "100.00",
      "apr": "9.90",
      "status": "Active",
      "created_at": "2026-11-26T10:00:00Z"
    }
  ],
  "total": 3,
  "limit": 20,
  "offset": 0,
  "has_more": false,
  "empty_state_message": null
}
```

### InstalmentPlanDetailResponse
```json
{
  "id": 1,
  "account_id": 1,
  "plan_reference": "IP-1",
  "plan_name": "IP-1 - 12 months",
  "original_amount": "1200.00",
  "remaining_balance": "800.00",
  "instalment_count": 12,
  "monthly_payment": "100.00",
  "apr": "9.90",
  "status": "Active",
  "source_transaction": null,
  "linked_category": {
    "category_id": 4,
    "category_name": "Instalment",
    "category_amount": "800.00"
  },
  "balance_effect": {
    "is_reflected_in_balance": true,
    "explanation": "The remaining balance of £800.00 is included in your total balance under the 'Instalment' category. Monthly instalments of £100.00 reduce this amount."
  },
  "created_at": "2026-11-26T10:00:00Z",
  "updated_at": "2026-11-26T10:00:00Z"
}
```

### TrackerItem
```json
{
  "entity_type": "Payment",
  "entity_id": "1",
  "title": "Payment of £100.00",
  "lifecycle_state": "Processing",
  "status_label": "Processing",
  "is_final": false,
  "amount": "£100.00",
  "last_updated_at": "2026-11-26T10:00:00Z",
  "freshness": {
    "level": "Current",
    "as_of": "2026-11-26T10:00:00Z"
  },
  "escalation": {
    "is_escalated": true,
    "reason": "Payment unresolved beyond expected timeframe",
    "guidance": "Please contact support if this persists."
  },
  "guidance": null,
  "resource_path": "/api/v1/payments/1"
}
```

### TrackerListResponse
```json
{
  "items": [ /* TrackerItem array */ ],
  "total": 10,
  "limit": 20,
  "offset": 0,
  "has_more": false,
  "unresolved_count": 3,
  "overall_message": null
}
```

### TrackerDetailResponse
```json
{
  "tracker_item": { /* TrackerItem */ },
  "milestones": [
    {
      "event_timestamp": "2026-11-26T09:00:00Z",
      "milestone_label": "Submitted",
      "detail": "Payment submitted"
    },
    {
      "event_timestamp": "2026-11-26T09:30:00Z",
      "milestone_label": "Processing",
      "detail": "Payment processing"
    }
  ],
  "timeline_freshness": {
    "level": "Current",
    "as_of": "2026-11-26T10:00:00Z"
  }
}
```

### TrackerRefreshResponse
```json
{
  "tracker_item": { /* TrackerItem */ },
  "refresh_outcome": "updated",
  "refresh_message": "Status updated successfully from external source."
}
```

## Seed Data

### Instalment Plans (ACC-1001)
- **IP-1**: £1200 original, £800 remaining, 12 months, £100/month, 9.90% APR, Active
- **IP-2**: £2400 original, £1800 remaining, 24 months, £100/month, 7.90% APR, Active
- **IP-3**: £600 original, £300 remaining, 6 months, £100/month, 0% APR, Active

IP-1 is linked to balance category "Instalment" via source_instalment_plan_id.

### Tracker Items
Existing seed data from TASK-5, TASK-7, TASK-8:
- **Payments**: PMT-1 to PMT-7 (various statuses with tracking events)
- **Money Transfers**: MT-1 to MT-4 (Submitted, Processing, Completed, Blocked)
- **Balance Transfers**: BT-1 to BT-7 (Submitted, ReviewRequired, Completed, Rejected)
- **Direct Debit Change Requests**: None seeded yet (domain exists for future tasks)

## Backend Flows

### Instalment Plan Visibility
1. GET /api/v1/instalments queries instalment_plans table filtered by account_id and status
2. Orders by created_at DESC (represents start_date in plan lifecycle)
3. Returns paginated list with plan_name computed as "{plan_reference} - {instalment_count} months"
4. GET /api/v1/instalments/{id} retrieves plan detail with:
   - linked_category: Queries balance_categories WHERE source_instalment_plan_id = plan.id
   - balance_effect: Computed based on linked_category presence
     - is_reflected_in_balance = true when linked category exists
     - explanation: Describes relationship to total balance and monthly reduction

### Status Tracker Aggregation
1. GET /api/v1/status-tracker aggregates TrackerItem from owning services:
   - Calls PaymentService.get_tracker_view() (via StatusTrackerRepository)
   - Calls MoneyTransferService.get_tracker_view() (via StatusTrackerRepository)
   - Calls BalanceTransferService.get_tracker_view() (via StatusTrackerRepository)
   - Calls DirectDebitService.get_tracker_view() (via StatusTrackerRepository)
2. Each service's get_tracker_view builds TrackerItem with:
   - Entity metadata (type, id, title, lifecycle_state, status_label, is_final)
   - Amount when applicable
   - Freshness from last_updated_at
   - Escalation when unresolved age > threshold OR status = Blocked/Restricted
   - Guidance for non-final/failed states (message_code, message, next_step)
   - resource_path to entity detail endpoint

### Escalation Thresholds
- **Payment**: 30 minutes for non-final states, immediate for Restricted
- **MoneyTransfer**: 60 minutes for non-final states, immediate for Blocked
- **BalanceTransfer**: 24 hours for non-final states, immediate for ReviewRequired
- **DirectDebitChangeRequest**: 24 hours for non-final states

### Tracker Detail with Timeline
1. GET /api/v1/status-tracker/{entity_type}/{id} retrieves entity from owning service
2. Builds TrackerItem (same logic as list aggregation)
3. Queries tracking_events WHERE entity_type = X AND entity_id = Y
4. Orders events by occurred_at ASC
5. Maps events to TrackerMilestone array: event_timestamp, milestone_label (status), detail (event_data)
6. Returns tracker_item + milestones + timeline_freshness

### Tracker Refresh
1. POST /api/v1/status-tracker/{entity_type}/{id}/refresh:
   - Checks throttle window (10 seconds per entity)
   - Returns 429 if within window
   - Calls FreshnessAndSyncService.sync_one(entity_type, entity_id, db)
2. FreshnessAndSyncService.sync_one (stub implementation):
   - Would call appropriate adapter based on entity_type (PaymentRailAdapter, MoneyTransferRailAdapter, etc.)
   - Stub simulates adapter call and records tracking event
   - Returns outcome: "success", "no_change", or "failed"
3. Maps sync outcome to refresh_outcome:
   - "success" → "updated" with message "Status updated successfully"
   - "no_change" → "unchanged" with message "No new information available"
   - "failed" → "failed" with limitation message
4. Returns updated TrackerItem + refresh_outcome + refresh_message

## Test Coverage
- **test_rewards_offers_instalments/test_instalments.py**: 7 tests covering instalment plan listing (success, pagination, empty state), detail (with/without linked category, balance effect explanation), not found, auth requirement
- **test_status_tracker/test_status_tracker.py**: 9 tests covering tracker list (success with mixed entities, unresolved filter, pagination), detail (with timeline, with escalation), refresh (success, throttle), not found, auth requirement

## Notes
- Instalment plan conversion (FR-INS-002) is deferred - source_transaction always returns null
- Tracker refresh uses stub sync adapter - real implementation would call external systems
- Escalation guidance is advisory only - no automated remediation
- Throttle window for refresh is 10 seconds per entity (in-memory tracking)
- Balance effect explanation explains relationship to total balance and category linkage

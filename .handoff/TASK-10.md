# TASK-10 Handoff Documentation: Support Diagnostics and Health Endpoints

## Overview

Backend Feature B8 implementation providing support diagnostics capabilities and health monitoring endpoints for operational supportability and troubleshooting.

## Mounted Endpoints

### Support Diagnostics

- **POST /api/v1/support-diagnostics/lookups**
  - Requires: Support role (email starting with "support")
  - Purpose: Perform diagnostic lookup for support investigations
  - Returns: Customer-visible state, lifecycle events, synchronization summary, risk decision (masked), and escalation context

- **GET /api/v1/support-diagnostics/operational-summary**
  - Requires: Support role (email starting with "support")
  - Query Parameters: `window_minutes` (5-1440, default 60)
  - Purpose: Operational metrics aggregation over time window
  - Returns: Auth failure rate, API error rate, latency P95, stale account count, invalid sync record rate, top failure categories
  - Note: No customer-identifying data included

### Health Monitoring

- **GET /api/health/live**
  - Requires: No authentication
  - Purpose: Liveness probe - confirms service process is running
  - Returns: `{"status": "ok", "checked_at": "<datetime>"}`
  - Status: Always 200

- **GET /api/health/ready**
  - Requires: No authentication
  - Purpose: Readiness probe - confirms service is ready to serve traffic
  - Checks: Database connectivity
  - Returns: `{"status": "ok", "checks": [...]}`
  - Status: 200 when healthy, 503 when database unavailable

## Request/Response Shapes

### DiagnosticLookupRequest

```json
{
  "verification_reference": "string (1-64 chars, required)",
  "lookup_reason": "string (1-200 chars, required)",
  "entity_type": "Account|Payment|MoneyTransfer|BalanceTransfer|DirectDebitChangeRequest (optional)",
  "entity_id": "string (required unless entity_type=Account)"
}
```

### DiagnosticLookupResponse

```json
{
  "lookup_id": "string (audit log ID)",
  "customer_visible_state": {
    "entity_type": "string",
    "entity_id": "string",
    "...": "entity-specific fields"
  },
  "lifecycle_events": [
    {
      "event_timestamp": "datetime",
      "event_type": "string",
      "status": "string",
      "source_system": "string|null",
      "source_event_reference": "string|null",
      "detail": "string|null"
    }
  ],
  "synchronization_summary": {
    "last_synchronized_at": "datetime|null",
    "sync_outcome": "string|null",
    "freshness_status": "string|null",
    "retry_count": "integer"
  },
  "risk_decision": {
    "decision": "allow|review|restrict",
    "reason_code": "string|null"
  } | null,
  "escalation_context": {
    "recommended_route": "payment_operations|transfer_operations|fraud_and_risk_review|none",
    "traceable_references": ["string"],
    "summary": "string|null"
  }
}
```

### OperationalSummaryResponse

```json
{
  "window_minutes": "integer",
  "auth_failure_rate": "float (percentage)",
  "api_error_rate": "float (percentage)",
  "api_latency_p95": "float (milliseconds)",
  "stale_account_count": "integer",
  "invalid_synchronized_record_rate": "float (percentage)",
  "top_failure_categories": [
    {
      "category": "string",
      "count": "integer"
    }
  ]
}
```

## Seed Data

### Support User Credentials

- **Email:** support@example.com
- **Password:** support123
- **Role:** Support (identified by email prefix "support")
- **Purpose:** Demo support user for testing diagnostic lookups and operational summary

## Backend Flows

### Diagnostic Lookup Flow

1. **Authentication & Authorization:**
   - Verify JWT token via middleware
   - Check support role (email starts with "support")
   - Return 403 if not support role

2. **Entity Resolution:**
   - If entity_type=Account or null: load account by entity_id
   - If other entity_type: load entity through StatusTrackingService.get_tracker_detail
   - Return 404 if entity not found
   - Return 422 if entity_id missing for non-Account entity

3. **State Reconstruction:**
   - Build customer_visible_state from entity fields
   - Query tracking_events for entity, ordered by occurred_at ASC
   - Query synchronization_records for latest sync status
   - Build lifecycle_events array with event details

4. **Escalation Context:**
   - Determine recommended_route based on entity type and state:
     - Payment (non-final/failed) → payment_operations
     - MoneyTransfer (non-final/failed/blocked) → transfer_operations
     - BalanceTransfer (non-final/rejected/review) → transfer_operations
     - DirectDebitChangeRequest (non-final/failed) → payment_operations
     - Risk decision review/restrict → fraud_and_risk_review
   - Collect correlation_id references from events
   - Generate summary message

5. **Audit Recording:**
   - Write audit_logs record BEFORE returning response (synchronous)
   - Action: support_lookup
   - Retention class: access_2y
   - Severity: info
   - Details include verification_reference, lookup_reason, entity_type, entity_id
   - Return lookup_id = audit_log.id

6. **Response:**
   - Return 201 with DiagnosticLookupResponse

### Operational Summary Flow

1. **Authentication & Authorization:**
   - Verify JWT token via middleware
   - Check support role
   - Return 403 if not support role

2. **Validation:**
   - Validate window_minutes in range [5, 1440]
   - Return 422 if out of range

3. **Metrics Aggregation:**
   - Calculate window_start = now - window_minutes
   - Query audit_logs for auth failures within window
   - Query metrics store for API error rates and latency (stub)
   - Query synchronization_records for stale counts
   - Aggregate top failure categories
   - **Important:** No customer-identifying data included

4. **Response:**
   - Return 200 with OperationalSummaryResponse

### Health Endpoints Flow

#### /health/live

- No authentication required
- No dependency checks
- Always return 200 with status=ok and checked_at timestamp
- Purpose: Kubernetes/orchestrator liveness probe

#### /health/ready

- No authentication required
- Execute database connectivity check: `SELECT 1`
- If database accessible:
  - Return 200 with status=ok and checks array
- If database unavailable:
  - Return 503 with status=unavailable and checks array with error details
- Purpose: Kubernetes/orchestrator readiness probe

## Role Enforcement

### Support User Access

Support users (email starting with "support"):
- **Allowed:**
  - POST /api/v1/support-diagnostics/lookups
  - GET /api/v1/support-diagnostics/operational-summary
  - GET /api/health/live
  - GET /api/health/ready

- **Denied (403):**
  - All domain endpoints: /api/v1/accounts/*, /api/v1/balance-breakdowns/*, /api/v1/transactions/*, /api/v1/payments/*, /api/v1/balance-transfers/*, /api/v1/money-transfers/*, /api/v1/direct-debits/*, /api/v1/offers/*, /api/v1/rewards/*, /api/v1/instalments/*, /api/v1/status-tracker/*

### Regular User Access

Regular users (non-support):
- **Allowed:**
  - All domain endpoints
  - GET /api/health/live
  - GET /api/health/ready

- **Denied (403):**
  - POST /api/v1/support-diagnostics/lookups
  - GET /api/v1/support-diagnostics/operational-summary

## Implementation Notes

### Security & Audit

- Every diagnostic lookup writes an audit event BEFORE returning the response
- Audit events use retention_class=access_2y (2 years retention)
- Risk decision details are masked in support view (only decision + reason_code shown)
- Operational summary contains NO customer-identifying data

### Freshness & Synchronization

- Synchronization summary shows latest sync status from synchronization_records
- Freshness classification determines data staleness
- Escalation context guides support routing based on state and age

### Health Monitoring

- /health/live is a simple process check (always succeeds if service is running)
- /health/ready tests actual database connectivity
- Both endpoints are unauthenticated for orchestrator access
- Ready endpoint returns 503 (not 500) when unhealthy to distinguish from application errors

## Testing Coverage

### test_diagnostic_lookup.py

- Happy path: Account entity lookup with support user
- Happy path: Payment entity lookup with tracking events
- Authorization: 403 for non-support users
- Not found: 404 for non-existent entity
- Audit: Verify audit event recorded before response

### test_operational_summary.py

- Happy path: Default 60-minute window
- Happy path: Custom window (120 minutes)
- Validation: Window bounds [5, 1440]
- Security: No PII in response
- Authorization: 403 for non-support users

### test_health_endpoints.py

- /health/live: Always returns 200 without auth
- /health/ready: Returns 200 when database accessible
- /health/ready: Returns 503 when database unavailable
- Both endpoints work without authentication

## Dependencies

- StatusTrackingService: For entity resolution and tracker detail
- AuditService: For synchronous audit event recording
- Middleware: For authentication and role checking
- Database models: CreditCardAccount, TrackingEvent, SynchronizationRecord, AuditLog

## Future Enhancements

The current implementation provides stub metrics for operational_summary. In production:

1. Query actual metrics store for:
   - Auth failure rate from audit_logs
   - API error rate from application metrics
   - API latency P95 from metrics/tracing system

2. Query synchronization_records for:
   - Stale account count (freshness_status != "Current")
   - Invalid sync record rate (sync_outcome = "Failed")

3. Aggregate top failure categories from:
   - Audit logs with severity=warning/error
   - Tracking events with failure statuses
   - Group by entity_type and status

4. Add adapter circuit state checks to /health/ready

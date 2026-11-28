# TASK-12 handoff: tracking events and data-rights requests

## Routes added (all under /api/v1, bearer token required)
GET /api/v1/accounts/{accountId}/tracking-events
- Query: trackedEntityType (account|transaction|payment), limit (1-100, default 25), offset.
- Customer only (administrator 403, foreign account 404, bad id or filter 422, no token 401).
- 200 `{items, total, limit, offset}`, ordered by occurredAt desc. Item: id, accountId, transactionId, paymentId, trackedEntityType, trackedEntityId, lifecycleStatus (verbatim), sourceTime (nullable), provenance, occurredAt, freshness {state, basis, sourceTime, maxAgeSeconds}.
- freshness.state is "freshness unavailable" (no sourceTime), "unconfirmed freshness" or "stale". Never fresh or real-time. No completion time is inferred.

POST /api/v1/data-rights-requests
- Header Idempotency-Key required (1-64 chars of letters, digits, - or _). Body `{requestType: export|deletion, subjectRef?}`.
- 201 new request; 200 replay with header `Idempotent-Replayed: true` (no second row or audit event); 400 same key with a different body; 403 customer naming another subject; 404 administrator with no or unknown subject; 422 invalid input; 401 no token.
- Response: id, subjectRef, requestType, status, requestedAt, dueAt (requestedAt + data_rights.fulfilment_days, 30), completedAt, outcomeSummary.
- Creates a row (status received) and the audit event data_rights_request_created in one transaction. It starts no export or deletion job.

GET /api/v1/data-rights-requests
- Query: status (received|in_progress|fulfilled|declined), limit, offset. Customer sees own requests, administrator sees all. 200 `{items, total, limit, offset}`, newest requestedAt first.

GET /api/v1/data-rights-requests/{requestId}
- 200 one request; 404 for other users' requests (administrator sees all); 422 malformed id.

## Seed
- ACC-1001 tracking: account "Open", transaction TXN-1 "Pending", payment PMT-1 "Processing" with no sourceTime (freshness unavailable).
- customer01: one received export and one fulfilled export (completedAt and outcomeSummary set). customer02 has none.
- Logins: customer01, customer02, admin01 (see app/seed_data/users.py). Administrator subjectRef values: CUS-1001, CUS-2001.

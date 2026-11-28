# TASK-4 handoff: cards and freshness

## Endpoint
GET /api/v1/accounts/{accountId}/cards  (bearer customer token; query limit 1-100 default 25, offset >=0)
- 200 `{items, total, limit, offset}`; item: `id, accountId, sourceRef, maskedPan, cardStatus, expiryMonthYear (YYYY-MM), isDigital`.
- `maskedPan` always starts `****`; `cardStatus` is the source value verbatim (Active | PendingActivation).
- 401 no token, 403 administrator, 404 foreign or unknown account, 422 malformed id.

## Seed
- CRD-1 on ACC-1001 (customer01): `**** 4821`, 2028-09, Active, isDigital false.
- CRD-3 on ACC-1003 (customer01): `**** 9040`, 2029-11, PendingActivation, isDigital null.
- ACC-1002 has no cards (empty list); ACC-2001 belongs to customer02 (404 for customer01).

## Backend building blocks
`FreshnessInterpreter(SettingsRepository, clock).for_kind("balance_breakdown"|"transaction"|"tracking_event", source_time)`
and static `interpret(source_time, max_age_seconds, now)` return `Freshness`
(states: freshness unavailable, unconfirmed freshness, stale; never fresh). Max ages are all `not_set` until approved.

# TASK-10 handoff: payment detail and information boundary

## Route added
GET /api/v1/payments/{paymentId}

- Bearer token required. 401 no token, 403 administrator, 404 unknown or foreign id (safe `{"detail": ...}`), 422 malformed id.
- 200 returns one Payment object (not a page), same shape as an item of GET /api/v1/accounts/{accountId}/payments:
  id, accountId, sourceRef, viaMandateRef, paymentType, paymentMethod, paymentStatus, paymentAmount (string), paymentDate,
  sourceBankName, sourceMaskedAccount (masked), freshness (always "freshness unavailable"), informationalNotice (fixed PAYMENT_NOTICE).
- Status and type are the stored source values, unchanged. The UI must show no payment or lifecycle-change control.

## Boundary
POST/PUT/PATCH/DELETE on /api/v1/payments*, /api/v1/transfers, /api/v1/payees, /api/v1/mandates return the safe 404 with no Allow header. No new operation was added to the OpenAPI allow-list beyond the payment detail GET.

## Seed
customer01 (ACC-1001) PMT-1..PMT-6 (all five statuses; PMT-6 has MND-1). Use login personas customer01, admin01 (403).

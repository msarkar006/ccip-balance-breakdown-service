# TASK-9 handoff: payment history

## Endpoint added
GET /api/v1/accounts/{accountId}/payments

Bearer token required (customer role). Query: paymentType (OneOff, Scheduled, DirectDebitCollection),
paymentStatus (Completed, Processing, Failed, Submitted, Cancelled), limit (1-100, default 25), offset (>=0).
Response 200: `{items, total, limit, offset}`, ordered by paymentDate descending, then id descending.

Each item: id, accountId, sourceRef, viaMandateRef (opaque text, null if none), paymentType, paymentMethod,
paymentStatus (verbatim), paymentAmount (string), paymentDate (YYYY-MM-DD calendar date), sourceBankName,
sourceMaskedAccount (starts with `****`, may be null), freshness (always `freshness unavailable`),
informationalNotice (fixed text).

Errors: 401 no token, 403 administrator, 404 foreign or unknown account, 422 bad id, filter, limit or offset.
No write methods are routed.

## Seed (customer01 / ACC-1001 has six; ACC-1002 has none)
- PMT-1 OneOff Completed 500.00 FasterPayments 2026-11-24
- PMT-2 OneOff Processing 121.56 DebitCard 2026-11-24
- PMT-3 OneOff Failed 2000.00 FasterPayments 2026-11-23 (Other Bank Ltd)
- PMT-4 Scheduled Submitted 300.00 2026-12-15
- PMT-5 Scheduled Cancelled 100.00 2026-11-30
- PMT-6 DirectDebitCollection Completed 121.56 DirectDebit 2026-10-30, viaMandateRef MND-1

## Transactions
The transaction schema already keeps `transactionTime` and `postedDate` as separate fields; `postedDate`
is null for Pending rows and is never fabricated.

## Note
`sourceBankName` is not in openapi.yaml's Payment schema but is shown in wireframe_05 and stored in the table, so it is returned.

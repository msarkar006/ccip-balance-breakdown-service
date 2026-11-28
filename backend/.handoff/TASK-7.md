# TASK-7 handoff: transactions list and balance qualifier notice

Bearer token required. Customer role only (administrator 403, foreign account 404, malformed id 422).

## Endpoint

GET /api/v1/accounts/{accountId}/transactions

Query: transactionStatus (Pending or Posted, optional), limit (1-100), offset (>=0).
Response: `{items, total, limit, offset}`. Ordered by transactionTime descending, then id descending.
Item: id, accountId, cardId (null), maskedPan (null or "**** 4821"), sourceRef, transactionStatus, transactionTime,
postedDate (null, never fabricated), transactionAmount (string), merchantName, merchantCategoryCode,
eligibleForInstalment (source indicator only), freshness {state, basis, sourceTime, maxAgeSeconds}.

## Changed (existing route GET /api/v1/balance-breakdowns/{breakdownId})

Each category gains `qualifierNotice` (string or null). It is set when the category carries an APR, promo end date,
revert rate or days to expiry, and says the values are information only, not a pricing promise or entitlement.

## Seed (login customer01)

ACC-1001: TXN-1 (Pending 42.15, TESCO STORES 4412, 14:05), TXN-2 (Pending 31.00), TXN-3 (Posted, posted 2026-11-21),
TXN-4 (Posted, eligibleForInstalment true). All on card **** 4821. ACC-1002: no transactions (empty state).

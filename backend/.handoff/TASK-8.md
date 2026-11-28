# TASK-8 handoff: transaction detail

Bearer token required. Customer role only (administrator 403, foreign or unknown id 404, malformed id 422, no token 401).

## Endpoint

GET /api/v1/transactions/{transactionId}

Response (single object, not a page): id, accountId, cardId, maskedPan (null or "**** 4821"), sourceRef,
transactionStatus (Pending or Posted), transactionTime, postedDate (null when the source gives none, never fabricated),
transactionAmount (string), merchantName, merchantCategoryCode, eligibleForInstalment (source indicator only),
freshness {state, basis, sourceTime, maxAgeSeconds}.

Freshness comes from transactionTime via FreshnessInterpreter: "unconfirmed freshness" by default,
"stale" once the approved max age is reached. The same freshness applies to list items.
Show transactionTime and postedDate as separate labelled fields; show "Not supplied" for a null postedDate.

## Seed (login customer01)

TXN-1 and TXN-2 Pending (no postedDate), TXN-3 Posted with postedDate 2026-11-21, TXN-4 Posted with eligibleForInstalment true.
Ids come from the list route GET /api/v1/accounts/{accountId}/transactions.

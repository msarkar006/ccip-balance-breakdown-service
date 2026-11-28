# TASK-5 handoff: balance breakdowns (FR-BAL-001, FR-BAL-002)

Auth: bearer token required. 401 no token, 403 administrator, 404 foreign/unknown id, 422 malformed id or paging.

## Endpoints
GET /api/v1/accounts/{accountId}/balance-breakdowns?limit=&offset=
- Returns `{items, total, limit, offset}`; limit 1-100 (default 25), offset >= 0.
- Items: `id, accountId, sourceRef, asOf, totalOutstanding, pendingTotal, isZeroBalance, freshness`.
- Order: `asOf` descending, null `asOf` last.

GET /api/v1/balance-breakdowns/{breakdownId}
- Returns `id, accountId, sourceRef, asOf, totalOutstanding, pendingTotal, isZeroBalance, purchasesSubtotal, balanceTransfersSubtotal, categories[], freshness, notice`.
- `categories` is not paged, ascending `displayRank`: `id, sourceRef, categoryType, categoryLabel, displayRank, categoryBalance, categoryAprPercent, promoEndDate, revertRatePercent, daysToExpiry, sourceBalanceTransferRef, sourceInstalmentPlanRef`.
- Money and percent are strings; absent values are null. `pendingTotal` is never merged into or relabelled as outstanding/posted.
- `freshness.state`: `freshness unavailable` (null asOf) or `unconfirmed freshness`.

## Seed (customer01 = synthetic.customer01 / Prototype!2026)
- BBD-1 on ACC-1001: asOf 2026-11-24T08:15Z, outstanding 4862.35, pending 114.20, purchases 1852.10, BT 3010.25, zero false; categories CAT-1..CAT-5 (rank 1-5; CAT-3 BT-1, CAT-4 BT-2, CAT-5 IP-66).
- BBD-2 on ACC-1002: zero balance true, outstanding 0.00, pending 4.80, asOf 2026-11-24T08:15Z, no categories.
- BBD-3 on ACC-1003: asOf missing (null), outstanding 7400.55, pending 0.00, category CAT-6.
- ACC-2001 (customer02) has none; customer02 gets 404 on customer01's ids.
Ids are generated UUIDs: read them from the list endpoint.

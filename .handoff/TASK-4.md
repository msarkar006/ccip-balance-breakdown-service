# TASK-4 Handoff: Balance Breakdown and Balance Transfer Offers

## Mounted Endpoints

### Balance Breakdowns

- **GET /api/v1/balance-breakdowns/current**
  - Query parameters: `account_id` (required)
  - Returns: Most recent balance breakdown snapshot for the account
  - Response includes:
    - `total_balance`: Total outstanding balance
    - `pending_total`: Sum of pending/unposted amounts (currently returns 0.00)
    - `categories`: Ordered list of balance categories
    - `freshness`: Freshness disclosure object with `level` and `as_of` timestamp
  - Categories are ordered by `display_rank` (ascending, nulls last)
  - Each category may include:
    - `source_link`: Object linking to source BalanceTransfer or InstalmentPlan if applicable

- **GET /api/v1/balance-breakdowns/{breakdown_id}/categories/{category_id}**
  - Path parameters: `breakdown_id`, `category_id`
  - Returns: Detailed category information
  - Response includes all category fields plus source linkage

### Offers

- **GET /api/v1/offers**
  - Query parameters:
    - `account_id` (required): Account ID
    - `context` (optional): Filter by offer type (BalanceTransfer, Rewards, Instalment)
    - `limit` (optional, default 20, max 100): Results per page
    - `offset` (optional, default 0): Pagination offset
  - Returns: Paginated offer list
  - Response envelope:
    - `items`: Array of offer objects
    - `total`: Total count of matching offers
    - `limit`: Requested limit
    - `offset`: Current offset
    - `has_more`: Boolean indicating more results available
  - Filters:
    - Only returns offers with `status` = "Available" or "Active"
    - Orders by `valid_from` descending

## Request/Response Shapes

### Balance Breakdown Response

```json
{
  "id": 1,
  "account_id": 123,
  "total_balance": "1799.50",
  "pending_total": "0.00",
  "snapshot_date": "2026-11-26T14:00:00Z",
  "categories": [
    {
      "id": 1,
      "category_name": "StandardPurchase",
      "category_amount": "299.50",
      "apr": "19.90",
      "display_rank": 1,
      "promo_rate": null,
      "promo_end_date": null,
      "source_link": null
    },
    {
      "id": 3,
      "category_name": "BalanceTransfer",
      "category_amount": "500.00",
      "apr": "0.00",
      "display_rank": 3,
      "promo_rate": "0.00",
      "promo_end_date": "2027-10-27T14:00:00Z",
      "source_link": {
        "source_type": "BalanceTransfer",
        "source_id": 1,
        "source_reference": "BT-2024-001"
      }
    }
  ],
  "freshness": {
    "level": "Current",
    "as_of": "2026-11-26T14:00:00Z"
  },
  "created_at": "2026-11-26T14:00:00Z",
  "updated_at": "2026-11-26T14:00:00Z"
}
```

### Category Detail Response

```json
{
  "id": 1,
  "breakdown_id": 1,
  "category_name": "StandardPurchase",
  "category_amount": "299.50",
  "apr": "19.90",
  "display_rank": 1,
  "promo_rate": null,
  "promo_end_date": null,
  "source_link": null,
  "created_at": "2026-11-26T14:00:00Z",
  "updated_at": "2026-11-26T14:00:00Z"
}
```

### Offer List Response

```json
{
  "items": [
    {
      "id": 1,
      "offer_code": "BT-PROMO-2024",
      "offer_title": "0% Balance Transfer for 12 months",
      "offer_description": "Transfer your balance and pay 0% interest for 12 months",
      "offer_type": "BalanceTransfer",
      "status": "Available",
      "valid_from": "2026-11-16T00:00:00Z",
      "valid_until": "2027-02-14T00:00:00Z"
    }
  ],
  "total": 6,
  "limit": 20,
  "offset": 0,
  "has_more": false
}
```

## Seed Balance Breakdown IDs

### Account ACC-1001 (****1001)

- **Balance Breakdown ID**: Auto-increment (typically ID 1 in fresh database)
- **Total Balance**: 1799.50
- **Categories**:
  1. StandardPurchase: 299.50 (display_rank: 1, APR: 19.90%)
  2. PromotionalPurchase: 200.00 (display_rank: 2, APR: 0.00%, promo until +90 days)
  3. BalanceTransfer: 500.00 (display_rank: 3, APR: 0.00%, linked to BT-2024-001, promo until +335 days)
  4. Instalment: 800.00 (display_rank: 4, APR: 9.90%, linked to IP-2024-001)

### Source Entities

- **Balance Transfer**: `BT-2024-001` (external_transfer_id)
  - Transfer amount: 500.00
  - Promotional rate: 0.00%
  - Promotional period: 12 months
  - Status: Completed
  
- **Instalment Plan**: `IP-2024-001` (plan_reference)
  - Original amount: 1200.00
  - Remaining balance: 800.00
  - Instalment count: 12
  - Monthly payment: 100.00
  - APR: 9.90%
  - Status: Active

## Seed Offer IDs

### Account ACC-1001 Offers

6 offers seeded with the following codes:

1. **BT-PROMO-2024**: 0% Balance Transfer for 12 months (BalanceTransfer, Available)
2. **BT-EXTENDED-2024**: 0% Balance Transfer for 18 months (BalanceTransfer, Available)
3. **BT-STANDARD-2024**: 3.9% Balance Transfer for 24 months (BalanceTransfer, Active)
4. **RWD-DOUBLE-2024**: Double Rewards Points (Rewards, Available)
5. **RWD-CASHBACK-2024**: 5% Cashback on Groceries (Rewards, Available)
6. **INS-FLEXI-2024**: Flexible Instalment Plan (Instalment, Available)

## Backend Flows

### Balance Breakdown Retrieval

1. `BalanceBreakdownService.get_current_breakdown(account_id)`
2. Repository queries for most recent breakdown by `snapshot_date DESC`
3. Repository retrieves categories ordered by `display_rank ASC NULLS LAST`
4. Service computes `pending_total` (currently stub returning 0.00)
5. Service queries `FreshnessAndSyncService` for freshness classification
6. For each category, service builds `source_link` if:
   - `source_balance_transfer_id` is set → queries BalanceTransfer table
   - `source_instalment_plan_id` is set → queries InstalmentPlan table
7. Returns structured response with categories and freshness

### Category Detail Retrieval

1. `BalanceBreakdownService.get_category_detail(breakdown_id, category_id)`
2. Repository queries for specific category
3. Service builds `source_link` using same logic as above
4. Returns detailed category response

### Offer Listing

1. `RewardsOffersInstalmentsService.list_offers(account_id, context, limit, offset)`
2. Repository builds query with filters:
   - `account_id` match (required)
   - `offer_type` match if `context` provided
   - `status IN ('Available', 'Active')`
3. Repository counts total matching offers
4. Repository applies pagination (`LIMIT`, `OFFSET`) and ordering (`valid_from DESC`)
5. Service constructs response with:
   - `items`: List of offer objects
   - `total`: Total count
   - `limit`, `offset`: Echo request parameters
   - `has_more`: Computed as `(offset + limit) < total`

## Database Schema Changes

### New Migration: 20261126_1400_add_balance_category_fields.py

Adds to `balance_categories` table:

- `display_rank` (Integer, nullable): Display order for categories
- `promo_rate` (Numeric(5,2), nullable): Promotional APR if applicable
- `promo_end_date` (DateTime(timezone=True), nullable): End date of promotional period
- `source_balance_transfer_id` (Integer, FK to balance_transfers.id, indexed, nullable)
- `source_instalment_plan_id` (Integer, FK to instalment_plans.id, indexed, nullable)

Both foreign keys have named constraints and indexes for query performance.

## Testing

### Balance Breakdown Tests (11 tests)

- Current breakdown retrieval (success, not found)
- Source linkage to balance transfers and instalments
- Category detail retrieval (success, not found)
- Zero balance handling
- Category ordering by display_rank
- Authentication requirement

### Offer Tests (11 tests)

- List all offers
- Filter by context (BalanceTransfer, Rewards, Instalment)
- Pagination (first, middle, last page with has_more)
- Empty results
- Status filtering (excludes Expired)
- Authentication requirement
- Invalid context handling

## Notes

- `pending_total` in balance breakdown is currently a stub returning 0.00; full implementation deferred
- Freshness classification always returns "Current" level (stub implementation in `FreshnessAndSyncService`)
- Offer conversion/acceptance endpoints are deferred to later tasks (TASK-7)
- Balance transfer initiation is deferred to later tasks (TASK-7)
- All endpoints require JWT authentication via `get_current_user` dependency

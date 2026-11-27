# TASK-8 Handoff: Balance Transfer Initiation and Money Transfer Initiation

## Mounted Endpoints

### Balance Transfer Initiation
- **POST /api/v1/balance-transfers**
  - Initiates a balance transfer
  - Headers: `Idempotency-Key` (required), `X-Step-Up-Proof` (required)
  - Request body: account_id, offer_code, transfer_amount, external_card_last4, provider_name, idempotency_key
  - Response: 201 with balance transfer outcome (Submitted/ReviewRequired/Rejected) + guidance
  - Idempotent replay: 200 with idempotent_replay=true when same key + payload
  - Step-up missing/stale: 403

### Payee List
- **GET /api/v1/payees**
  - Lists customer-owned payees with masked sort code and account number
  - Query parameters: limit (1-100, default 25), offset (default 0)
  - Response: paginated payee list with masked details

### Money Transfer Initiation
- **POST /api/v1/money-transfers**
  - Initiates a money transfer
  - Headers: `Idempotency-Key` (required), `X-Step-Up-Proof` (required)
  - Request body: account_id, payee_id, amount, currency, idempotency_key
  - Response: 201 with money transfer outcome (Submitted/Processing/Rejected/Blocked) + guidance
  - Idempotent replay: 200 with idempotent_replay=true when same key + payload
  - Step-up missing/stale: 403

### Rewards Summary
- **GET /api/v1/rewards**
  - Returns rewards programme summary with points balance and servicing-relevant offers
  - Query parameters: account_id (required)
  - Response: programme object (null when absent) + relevant_offers array filtered by context=rewards_and_offers
  - Empty state: programme: null, relevant_offers: []

## Request/Response Shapes

### Balance Transfer Initiation Request
```json
{
  "account_id": 1,
  "offer_code": "BT-PROMO-2024",
  "transfer_amount": 500.00,
  "external_card_last4": "1234",
  "provider_name": "Example Bank",
  "idempotency_key": "bt-unique-key-123"
}
```

### Balance Transfer Initiation Response
```json
{
  "id": 8,
  "external_transfer_id": "BT-EXT-ABC123",
  "transfer_amount": 500.00,
  "status": "Submitted",
  "guidance": null,
  "idempotent_replay": false
}
```

### Payee List Response
```json
{
  "items": [
    {
      "id": 1,
      "payee_name": "John Smith",
      "account_number_masked": "****5678",
      "sort_code_masked": "12-**-56",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 3,
  "limit": 25,
  "offset": 0,
  "has_more": false
}
```

### Money Transfer Initiation Request
```json
{
  "account_id": 1,
  "payee_id": 1,
  "amount": 100.00,
  "currency": "GBP",
  "idempotency_key": "mt-unique-key-456"
}
```

### Money Transfer Initiation Response
```json
{
  "id": 5,
  "external_transfer_id": "MT-EXT-XYZ789",
  "amount": 100.00,
  "currency": "GBP",
  "status": "Submitted",
  "guidance": null,
  "idempotent_replay": false
}
```

### Rewards Summary Response
```json
{
  "programme": {
    "programme_name": "Rewards Plus",
    "points_balance": 1250,
    "status": "Active",
    "as_of": "2024-11-26T12:00:00Z"
  },
  "relevant_offers": [
    {
      "id": 4,
      "offer_code": "RWD-DOUBLE-2024",
      "offer_title": "Double Rewards Points",
      "offer_type": "Rewards",
      "status": "Available"
    }
  ],
  "freshness": {
    "level": "Current",
    "as_of": "2024-11-26T12:00:00Z"
  }
}
```

## Seed Data

### Demo Payees (Customer CUST-001, Account ACC-1001)
- Payee 1: John Smith, account ****5678, sort 12-**-56
- Payee 2: Jane Doe, account ****9012, sort 34-**-78
- Payee 3: ACME Corp, account ****3456, sort 56-**-90

### Demo Rewards Programme
- ACC-1001: Rewards Plus programme, 1250 points, Active status
- ACC-1002: null programme (no rewards programme)

## Backend Flows

### Balance Transfer Initiation
Executes `HighRiskWritePipeline`:
1. Ownership check (verify user owns account)
2. Step-up verification (scope: balance_transfer, lifetime 300s)
3. Schema validation (Pydantic + external_card_last4 length check)
4. Idempotency lookup (return existing if same key + payload)
5. Business rules validation:
   - Offer eligibility (BalanceTransfer offer, Available/Active status)
   - Amount > 0
   - Amount ≤ available_credit
6. Risk decision (FraudAndRiskAdapter.assess_balance_transfer)
   - allow → Submitted, submit to BalanceTransferRailAdapter
   - review → ReviewRequired, no source call
   - restrict → Rejected, no source call
7. Atomic commit (BalanceTransfer + idempotency key + first tracking event)
8. Publish servicing.balance_transfer.submitted event
9. Write financial_7y audit event
10. Return 201 with outcome + guidance

### Money Transfer Initiation
Executes `HighRiskWritePipeline`:
1. Ownership check (verify user owns account)
2. Step-up verification (scope: money_transfer, lifetime 300s)
3. Schema validation (Pydantic)
4. Idempotency lookup (return existing if same key + payload)
5. Business rules validation:
   - Payee ownership (verify payee belongs to user's customer)
   - Amount > 0
   - Amount + fee ≤ available_credit (fee stub = 0 for now)
6. Risk decision (FraudAndRiskAdapter.assess_money_transfer)
   - allow → Submitted, submit to MoneyTransferRailAdapter
   - review → Blocked, no source call
   - restrict → Rejected, no source call
7. Atomic commit (MoneyTransfer + idempotency key + first tracking event)
8. Publish servicing.money_transfer.submitted event
9. Write financial_7y audit event
10. Return 201 with outcome + guidance

### Rewards Summary
Retrieves rewards programme for account and filters offers by context=rewards_and_offers:
1. Query RewardsProgramme by account_id (null if not found)
2. Query Offer by account_id, offer_type=Rewards, status IN (Available, Active), context filter
3. Return programme object (null when absent) + relevant_offers array
4. Empty state: programme: null, relevant_offers: []
5. Freshness: stub returning "Current" with current timestamp

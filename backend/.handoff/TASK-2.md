# TASK-2 handoff: identity, session, accounts

All routes are mounted under `/api/v1`. Errors are `{"detail": "..."}` only. JSON keys are camelCase.
Every response carries `X-Correlation-ID` (send your own, 8-64 chars of `A-Za-z0-9._-`, to reuse it).

## Endpoints
POST /api/v1/auth/login
- Public. Body `{username, password}` (both required, extra keys rejected with 422).
- 200 `{accessToken, tokenType: "Bearer", issuedAt, expiresAt, inactivityTimeoutMinutes, user: {id, username, role, customerId}}`. The token is shown once.
- 401 `{"detail":"Invalid username or password"}` for unknown user, wrong password or inactive user (same text).
- 429 `{"detail":"Too many sign-in attempts"}` with a `Retry-After` header after 5 failures from one IP in 15 minutes, even with the right password.
- Creates a session and a `login_success` audit event; failures write `login_failure`.

POST /api/v1/auth/logout
- Bearer token. 204, no body. Revokes the session (reason `logout`) and writes a `logout` audit event. The token is 401 afterwards.

GET /api/v1/auth/session
- Bearer token. 200 `{user: {id, username, role, customerId}, issuedAt, expiresAt, lastActivityAt}`.
- Any missing, invalid, revoked, expired or inactive (over 15 minutes) token returns 401 `{"detail":"Authentication required"}`.

GET /api/v1/accounts
- Customer role only (administrator gets 403). Query `limit` (1-100, default 25), `offset` (default 0).
- 200 `{items: [Account], total, limit, offset}`, only the caller's accounts.

GET /api/v1/accounts/{accountId}
- Customer role only. `accountId` is a UUID (422 otherwise). An account owned by someone else returns 404 `{"detail":"Resource not found"}`.

## Account shape
`id, sourceRef, productName, accountStatus, openedOn, currency, creditLimit, availableCredit, currentBalance, standardPurchaseApr, lastStatementBalance, nextStatementDate, paymentDueDate, minimumPayment, freshness, informationalNotice`
- Money is a string with 2 decimals (`"4862.35"`); APR is a string without trailing zeros (`"22.9"`); dates are `YYYY-MM-DD`.
- Absent values are `null` (never 0). Show `Not supplied`.
- `freshness` is always `{state: "freshness unavailable", basis, sourceTime: null, maxAgeSeconds: null}` for accounts.
- Show `nextStatementDate` beside `lastStatementBalance` and `paymentDueDate` beside `minimumPayment`.

## Seed logins (password `Prototype!2026`)
- synthetic.customer01 (customer): ACC-1001 (limit 10000.00, available 5137.65, balance 4862.35, statement 4701.10, minimum 121.56, APR 22.9, next statement 2026-12-05, due 2026-12-30, Open, opened 2021-03-18); ACC-1002 (zero balance, no due date or minimum); ACC-1003 (mostly null fields, for the "Not supplied" state).
- synthetic.customer02 (customer): ACC-2001, a foreign account for 404 tests.
- synthetic.admin01 (administrator): `customerId` is null; accounts return 403.

Seed: `python -m app.seed` (needs `SEED_ENABLED=true`, idempotent). Run after `alembic upgrade head`.

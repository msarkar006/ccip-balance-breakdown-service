# AGENTS.md — ccip-balance-breakdown-service

Sources: codebase, HLD, Verify result and report files. Test names cited under the rules are the files that cover them; their contents were not re-checked line by line (unverified). Commands below are copied from the files named beside them ("declared, not run").

## What this is

An information-only credit-card servicing prototype. A React + Vite + Carbon frontend reads dated balance breakdowns, transactions, payments, tracking events and data-rights status from one stateless FastAPI backend over one database (SQLite locally, PostgreSQL in containers, CI and k8s). It shows source values with their time and freshness and never performs a financial action. Data is approved synthetic data.

## Layout

| Path | Owns |
|---|---|
| `backend/app/main.py` | App factory. Mounts `health` at the root and every other router under `API_PREFIX = "/api/v1"`. Middleware: correlation id, metrics, security headers, CORS. |
| `backend/app/routers/` | HTTP layer: `auth`, `accounts`, `balances`, `transactions`, `payments`, `tracking`, `data_rights`, `health`. |
| `backend/app/services/` | Business logic: account, auth, audit, balance, data_rights, freshness_interpreter, login_rate_limiter, ownership, payment, tracking, transaction. |
| `backend/app/repositories/` | One repository per aggregate; all database access. |
| `backend/app/models/`, `schemas/` | SQLAlchemy models; Pydantic DTOs. |
| `backend/app/config.py` | Typed `Settings` (`get_settings()`). |
| `backend/app/seed.py`, `seed_data/` | Idempotent synthetic seed (`python -m app.seed`). |
| `backend/alembic/` | Migrations (`versions/0001_baseline.py`). |
| `backend/tests/` | pytest suite; `tests/integration/test_journey.py` is the cross-domain journey. |
| `frontend/src/` | `pages/`, `components/`, `lib/` (`api-client.ts`, `auth-context.tsx`, `queries.ts`, `format.ts`), `types/`, `test/`. |
| `tests/e2e/` | Playwright specs (login, journeys, one spec per wireframe). |
| `infra/k8s/` | Kustomize `base/` plus `overlays/{dev,staging,prod}`; see `infra/k8s/README.md`. |
| `.github/workflows/ci.yml` | CI: backend, frontend, images jobs. |

Stack (from manifests): Python >=3.11 (CI uses 3.12), FastAPI >=0.110, SQLAlchemy >=2.0, Alembic >=1.13, Pydantic >=2.6, PyJWT, bcrypt, optional `psycopg[binary]>=3.2` (`backend/pyproject.toml`). Node `^20.19.0 || >=22.12.0`, React 18.3, react-router-dom 6, Vite 6, Vitest 2, TypeScript 5.7, Carbon (`@carbon/react`), Tailwind 3, Playwright (`frontend/package.json`). PostgreSQL image `postgres:16.4-alpine`.

Frontend routes (`frontend/src/App.tsx`): login, `/accounts`, `/accounts/:accountId/balance`, `/accounts/:accountId/transactions`, `/accounts/:accountId/payments`, `/data-status`, `/data-rights`; unknown paths redirect to `/accounts`.

## Run it

Required: Python 3.11+, Node 20.19+ or 22.12+ with npm. Docker is optional.

- Everything locally: `./start.sh` (`start.sh`). It creates `backend/.venv`, copies `backend/dev.env` to `backend/.env` once, runs `pip install . -q`, `alembic upgrade head`, `python -m app.seed`, starts uvicorn, then `npm ci` and Vite. Stop with `./stop.sh`, which kills only the PIDs in `.pids`. `start.bat` / `stop.bat` wrap these for Windows (Git Bash).
- Ports: `start.sh` takes the first free port from 9000 for the backend and from 5173 for the frontend, and prints the URLs. The Vite `/api` proxy reads `BACKEND_PORT` (`frontend/vite.config.ts`). Logs go to `$TMPDIR/ccip-balance-breakdown` (`backend.log`, `frontend.log`).
- Backend only: `backend/run.sh` (`PORT`, default 9000). Frontend only: `frontend/run.sh` (`PORT` default 5173, `BACKEND_PORT` default 9000).
- Docker: `docker compose up --build` (`docker-compose.yml`; backend `8000`, frontend nginx `80`, SQLite on the `app-data` volume). PostgreSQL: `docker compose -f docker-compose.yml -f docker-compose.postgres.yml up --build` (`docker-compose.postgres.yml`, reads `POSTGRES_PASSWORD`). `backend/docker-entrypoint.sh` runs `alembic upgrade head` then `python -m app.seed` before the server.
- URLs: API under `/api/v1`; `GET /health` and `GET /health/ready` (outside `/api`); `/docs` and `/openapi.json` only when `DEBUG=true` or the environment is non-deployed.

## Test, lint, build (declared in `.github/workflows/ci.yml` and `frontend/package.json`)

Backend (from `backend/`): `pip install ".[dev,postgres]"`, `ruff check app tests`, `mypy app`, `pytest -q --cov=app --junitxml=pytest-report.xml`.
- One file: `pytest tests/test_balances.py`. One test: `pytest tests/test_balances.py -k <name>`.
- Tests use a temporary SQLite file built once from the real Alembic migrations; each test gets a copy (`backend/tests/conftest.py`). It forces `ENVIRONMENT=test`, `SEED_ENABLED=false`. Extend `conftest.py`; do not add a second database setup.
- CI also runs `alembic upgrade head` and `python -m app.seed` against PostgreSQL with `DATABASE_URL`.

Frontend (from `frontend/`): `npm ci`, `npx eslint src` (`npm run lint`), `npx tsc --noEmit` (`npm run typecheck`), `npx vitest --run` (`npm test`), `npm run build`. One file: `npx vitest --run src/pages/LoginPage.test.tsx`.

E2E (Playwright, from `frontend/`): `npm run e2e`. `playwright.config.ts` starts both servers itself (`testDir` is `../tests/e2e`): it runs `alembic upgrade head`, `python -m app.seed`, uvicorn on `E2E_BACKEND_PORT` (default 9100) with a SQLite file `e2e.db`, and `npm run dev` on `E2E_FRONTEND_PORT` (default 5173, strict). Those ports must be free; `reuseExistingServer` is false. `E2E_PYTHON` selects the interpreter. The Python dependencies must already be installed.

## Rules the next agent must not break

1. **Stay information-only. Add no route that creates, changes, schedules, cancels or moves money or servicing records.** The only mutating routes are `POST /api/v1/auth/login`, `POST /api/v1/auth/logout` and `POST /api/v1/data-rights-requests`; the data-rights POST only writes an audited request record. Reason: the product must not imply or perform financial actions. Check: `backend/tests/test_openapi_allowlist.py` (exact route allow-list), `backend/tests/test_information_boundary.py`. If you add a route, it needs a GET and an allow-list entry. [HLD, code]
2. **Label no UI control with a financial-action verb.** Reason: the UI must not offer actions. Check: `frontend/src/test/forbidden-verbs.test.ts` scans every `.tsx` outside `test/`. [HLD, code]
3. **Do not compute, merge or relabel financial values or times.** Balances, subtotals and categories are separate fields shown as the source supplies them; `asOf`, transaction time, posted time, payment date, statement and due dates stay distinct and UTC-aware; status text is passed through verbatim; do not fabricate a posted time. Reason: combining or relabelling values changes their financial meaning. Check: `backend/tests/test_balances.py`, `test_transactions_list.py`, `test_payments_list.py`, `test_tracking.py`. [HLD]
4. **Respect the layering: routers call services; services call repositories; routers do not import repositories.** Reason: keeps access control and rules in one place. Check: grep `repositories` in `backend/app/routers/` returns nothing. [HLD, code]
5. **Scope every domain query to the authenticated customer.** Another customer's resource returns 404, not 403. Use the `ownership` service and the single `get_current_user` dependency (`backend/app/dependencies.py`). The administrator role is limited to the data-rights workflow; the frontend `AppShell` skips the accounts query for administrators because `GET /accounts` returns 403 for them. Check: `backend/tests/test_accounts.py`, `test_auth.py`, `test_sessions.py`. [HLD, code]
6. **Errors are `{"detail": "..."}` from the central handlers in `backend/app/middleware/error_handlers.py`.** Never return stack traces or internal text. Check: `backend/tests/test_auth.py`, `test_health.py`. [HLD, code]
7. **Store and return masked values only** (card `**** 4821`, payment source `****1234`). Never store a full card or account number, a raw session token (only a hash), or a plaintext password (bcrypt). Never log secrets. Check: `backend/tests/test_cards.py`, `test_sessions.py`, `test_audit.py`. [HLD]
8. **Read environment variables only in `backend/app/config.py`.** `Settings` validates at startup: outside `development`/`local`/`test`, `JWT_SECRET_KEY` must be 32+ characters and not a `replace-with…`/`dev-only…` placeholder; `CORS_ORIGINS` must be an explicit list and `*` is rejected. `ENVIRONMENT` defaults to `production`. Reason: unsafe config must fail at boot. [code]
9. **Change the schema only through Alembic migrations in `backend/alembic/versions/`.** Never `create_all`. Add one with a new revision file; `ruff` excludes that folder. Check: `backend/tests/test_migrations.py`, `test_pipeline_migration_parity.py`. [HLD, code]
10. **Seed data is synthetic, idempotent and gated by `SEED_ENABLED`.** Never enable it against real data or auto-seed production. Check: `backend/tests/test_pipeline_seed_runs.py`. [HLD, code]
11. **All frontend HTTP goes through `frontend/src/lib/api-client.ts`.** It has only `get` and `post`, base `VITE_API_URL ?? '/api/v1'`; leave `VITE_API_URL` unset, so the browser calls relative `/api` (Vite proxy in dev, nginx in the container via `frontend/nginx.conf.template`). Do not repeat `/api/v1` in call paths. [HLD, code]
12. **Pagination is limit/offset on unbounded lists; routes use plural nouns nested at most one level.** [HLD]
13. **Deferred scope — do not implement; out of scope for this release:** FR-BAL-004, FR-TRN-004, FR-BTR-001..003 (balance transfers), FR-MTR-001..003 (money transfers, payees), FR-DDM-001..003 (direct-debit mandates), FR-RWD-001..002 (rewards), FR-OFR-001..003 (offers), FR-INS-001..003 (instalments). Source zero-balance and instalment-eligibility indicators appear only as labelled source fields. [HLD]

## API surface (`backend/app/routers/`)

All under `/api/v1` unless noted. Auth: `POST /auth/login`, `POST /auth/logout`, `GET /auth/session`. `GET /accounts`, `GET /accounts/{account_id}`, `GET /accounts/{account_id}/cards`, `GET /accounts/{account_id}/balance-breakdowns`, `GET /balance-breakdowns/{breakdown_id}`, `GET /accounts/{account_id}/transactions`, `GET /transactions/{transaction_id}`, `GET /accounts/{account_id}/payments`, `GET /payments/{payment_id}`, `GET /accounts/{account_id}/tracking-events`, `POST` and `GET /data-rights-requests`, `GET /data-rights-requests/{request_id}`. Root: `GET /health`, `GET /health/ready`. The data-rights POST accepts an `Idempotency-Key` header. Login failures are rate-limited (429) by `services/login_rate_limiter.py`. The running app exposes the live contract at `/openapi.json` when docs are enabled.

## How to add things

- **Endpoint:** schema in `schemas/`, repository method in `repositories/`, service in `services/`, router in `routers/`, include the router in `API_ROUTERS` in `main.py`, add it to `ALLOWED_OPERATIONS` in `backend/tests/test_openapi_allowlist.py`, add a test file in `backend/tests/`, mirror the DTO in `frontend/src/types/`.
- **Migration:** add a model in `models/`, then a new file in `backend/alembic/versions/` (template `script.py.mako`), run `alembic upgrade head`. Update `seed_data/` and `seed.py` if seed rows are needed.
- **Page:** page in `frontend/src/pages/`, components in `frontend/src/components/<area>/`, query in `lib/queries.ts`, route inside the authenticated block of `frontend/src/App.tsx`, a `*.test.tsx` beside the page, and a spec in `tests/e2e/` if it is a wireframe screen.

## Configuration (names only; `.env.example` documents each, `backend/dev.env` holds local development values)

`ENVIRONMENT`, `DEBUG`, `DATABASE_URL` (default `sqlite:///./app.db`), `JWT_SECRET_KEY`, `CORS_ORIGINS`, `SEED_ENABLED`, `LOG_LEVEL` (`DEBUG`..`CRITICAL`; raise to `DEBUG` for more detail), `OTEL_EXPORTER_ENDPOINT` (optional), `POSTGRES_PASSWORD` (compose Postgres only), `BACKEND_PORT` / `PORT` (local scripts). E2E: `E2E_BACKEND_PORT`, `E2E_FRONTEND_PORT`, `E2E_DATABASE_URL`, `E2E_PYTHON`, `E2E_TEST_TIMEOUT`, `E2E_ACTION_TIMEOUT`, `E2E_NAVIGATION_TIMEOUT`. Never commit real values; `backend/.env` is git-ignored.

## Seed data and reset

`python -m app.seed` (from `backend/`) loads synthetic users, accounts, cards, balances, transactions, payments, tracking events and data-rights requests, only when `SEED_ENABLED=true`; from the code it looks designed to be re-runnable (upsert/existence checks, unverified). Users: `synthetic.customer01` (customer, 3 accounts), `synthetic.customer02` (customer), `synthetic.admin01` (administrator). Passwords are defined in `backend/app/seed_data/users.py` and printed by `start.sh`. Reset local data: stop services, delete the SQLite file (`backend/app.db` by default; `backend/e2e.db` for e2e), then run `alembic upgrade head` and the seed again. For Docker, remove the `app-data` (or `pg-data`) volume.

## Reports and results

- `.verification/pytest.xml` (239 tests), `.verification/vitest.xml` (94 tests), `.verification/playwright.xml` (12 specs): all recorded with zero failures and zero skipped. `.verification/archive/` holds an earlier run. `backend/reports/junit.xml` is an earlier backend run.
- Pass summaries are in `.pass_summaries/`.
- `pytest` skip markers in `backend/tests/test_pipeline_*.py` are conditional guards that fire only if migrations or the seed fail.

## Known issues (from the Verify security report)

- `npm audit` on the frontend reports vulnerabilities: dev-only tooling (vitest chain, esbuild) and a moderate `react-router` 6.x advisory at runtime. Fixes need major bumps (vitest 5, react-router 7) and were not applied.
- `ruff` with bandit `S` rules reported 20 findings that were not triaged, including S310 (`urlopen`), S608 (SQL string) and S110 (`try/except/pass`). `ruff check app tests` in CI is the gate; re-check its current output.

## Open gaps

- The HLD writes the frontend base as `import.meta.env.VITE_API_URL ?? '/api'` with `/v1/...` appended per call. The code sets `API_BASE` to `'/api/v1'` and calls paths such as `/accounts`. The code is correct; the effective URLs are the same.

## Pointers to the plan

Per-task build notes are in `backend/.handoff/` and `.pass_summaries/`. `README.md` and `infra/k8s/README.md` describe running and deploying.

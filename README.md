# CCIP Balance Breakdown Service

Information-only credit-card servicing prototype: React + Vite + Carbon frontend, one stateless FastAPI
backend, one database (SQLite locally, PostgreSQL in containers/CI/staging/prod). No financial actions,
broker or queue.

## Run locally (SQLite, no Docker)

Needs Python 3.11+, Node 20.19+/22.12+.

    ./start.sh     # venv, pip install ., alembic upgrade head, seed, picks ports, starts both
    ./stop.sh      # stops only the PIDs in .pids

`start.sh` picks the backend port from 9000 and the frontend from 5173, exports `BACKEND_PORT` (read by the
Vite `/api` proxy) and `CORS_ORIGINS`. It copies `backend/dev.env` to `backend/.env` once. Logs: `$TMPDIR/ccip-balance-breakdown`.

Each service runs alone: `backend/run.sh` (`PORT`, default 9000) and `frontend/run.sh` (`PORT` default 5173,
`BACKEND_PORT` default 9000). On Windows use Git Bash (`start.bat` wraps `start.sh`).

## URLs

- Frontend: `http://localhost:5173` (calls relative `/api`)
- API: `/api/v1/...`; health `GET /health`, readiness `GET /health/ready` (database check; outside `/api`)
- Docs: `/docs`, `/openapi.json` only when `DEBUG=true`

## Seeded credentials (synthetic; password `Prototype!2026`)

| Username | Role |
|---|---|
| `synthetic.customer01` | customer (3 accounts) |
| `synthetic.customer02` | customer |
| `synthetic.admin01` | administrator (data rights page only) |

## Docker

    docker compose up --build                                   # SQLite on the /data volume, http://localhost
    docker compose -f docker-compose.yml -f docker-compose.postgres.yml up --build   # PostgreSQL 16

The backend entrypoint runs `alembic upgrade head` then the idempotent seed. nginx in the frontend image
proxies `/api/` to `BACKEND_HOST` (default `backend`, port 8000).

## Configuration

Every variable is documented in `.env.example` (required, default, where to obtain). Local values live in
`backend/dev.env`. Outside `development`/`local`/`test`, `JWT_SECRET_KEY` must be a real 32+ character secret.

| Variable | Required | Default |
|---|---|---|
| `ENVIRONMENT` | deployments | `production` |
| `DEBUG` | no | `false` |
| `DATABASE_URL` | no | `sqlite:///./app.db` |
| `JWT_SECRET_KEY` | yes | none |
| `CORS_ORIGINS` | no | `http://localhost:5173` |
| `SEED_ENABLED` | no | `false` |
| `LOG_LEVEL` | no | `INFO` |
| `OTEL_EXPORTER_ENDPOINT` | no | empty |
| `POSTGRES_PASSWORD` | postgres override | `ccip-local-password` |

## Tests and CI

    cd backend && .venv/bin/python -m pytest -q && ruff check app tests && mypy app
    cd frontend && npx eslint src && npx tsc --noEmit && npx vitest --run && npm run build

`.github/workflows/ci.yml` runs these, applies migrations and seed on PostgreSQL, and builds the images.

## Deploy and environments

`infra/` holds provider-neutral Kubernetes (kustomize) manifests with `dev`, `staging` and `prod` overlays;
see `infra/README.md`. Keep secrets out of git, `SEED_ENABLED=false` and `DEBUG=false` in prod.

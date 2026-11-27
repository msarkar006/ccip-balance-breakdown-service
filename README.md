# CCIP Balance Breakdown Service

A digital credit card servicing platform providing comprehensive servicing capabilities for credit card customers and support staff. The platform supports account overview, balance breakdown, transactions, payments, transfers, rewards, offers, instalments, and unified status tracking.

## Tech Stack

### Backend
- **Framework**: FastAPI 0.115+
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic 1.13+
- **Authentication**: JWT with bcrypt password hashing
- **Database**: SQLite (local/base) or PostgreSQL (production)

### Frontend
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite 6+
- **UI Library**: IBM Carbon Design System 1.72+
- **Routing**: React Router 6+
- **Styling**: Tailwind CSS 3.4+ with Carbon Design tokens
- **Testing**: Vitest (unit), Playwright (E2E)

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 20.19+ or 22.12+
- **npm**: Latest version (comes with Node.js)
- **Git Bash** (Windows only): For running shell scripts

## Project Structure

```
ccip-balance-breakdown-service/
├── backend/                  # FastAPI backend
│   ├── app/                 # Application code
│   │   ├── auth/           # Authentication domain
│   │   ├── accounts/       # Account overview
│   │   ├── balance_breakdowns/  # Balance breakdown
│   │   ├── transactions/   # Transaction history
│   │   ├── payments/       # Payment management
│   │   ├── balance_transfers/  # Balance transfers
│   │   ├── money_transfers/    # Money transfers
│   │   ├── direct_debits/      # Direct debit management
│   │   ├── rewards_offers_instalments/  # Rewards, offers, instalments
│   │   ├── status_tracker/     # Unified status tracking
│   │   ├── support_diagnostics/  # Support diagnostics
│   │   ├── audit/          # Audit service
│   │   ├── sync/           # Freshness and sync service
│   │   ├── adapters/       # External system adapters
│   │   ├── middleware/     # Auth and logging middleware
│   │   ├── core/           # Core utilities
│   │   └── models/         # SQLAlchemy models
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   ├── pyproject.toml      # Python dependencies
│   └── dev.env             # Development configuration
├── frontend/               # React frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   ├── components/     # Reusable UI components
│   │   ├── lib/            # Utilities and API client
│   │   └── __tests__/      # Unit tests
│   ├── e2e/                # End-to-end tests
│   └── package.json        # Node dependencies
├── start.sh                # Start script (Linux/macOS/Windows)
├── stop.sh                 # Stop script
├── start.bat               # Windows wrapper for start.sh
├── stop.bat                # Windows wrapper for stop.sh
├── docker-compose.yml      # Docker Compose (SQLite)
└── docker-compose.postgres.yml  # Docker Compose override (PostgreSQL)
```

## Quick Start

### 1. Local Development (Recommended)

Start the application with one command:

```bash
# Linux/macOS
./start.sh

# Windows (Git Bash)
start.bat
```

The script will:
- Check prerequisites (Python 3.11+, Node.js 20.19+/22.12+)
- Create Python virtual environment (if missing)
- Install backend dependencies
- Run database migrations
- Seed demo data
- Start backend on http://127.0.0.1:9000
- Install frontend dependencies
- Start frontend on http://127.0.0.1:5173

**Access the application:**
- Frontend: http://127.0.0.1:5173
- Backend API: http://127.0.0.1:9000
- API Documentation: http://127.0.0.1:9000/docs

**Stop all services:**

```bash
# Linux/macOS
./stop.sh

# Windows (Git Bash)
stop.bat
```

### 2. Docker Deployment (SQLite)

Build and run with Docker Compose:

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop services
docker compose down
```

**Access the application:**
- Frontend: http://localhost
- Backend API: http://localhost:9000
- API Documentation: http://localhost:9000/docs

### 3. Docker Deployment (PostgreSQL)

For production-like setup with PostgreSQL:

```bash
# Build images with PostgreSQL support
docker compose -f docker-compose.yml -f docker-compose.postgres.yml build

# Start services (database, backend, frontend)
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d

# Check database migration status
docker compose exec backend alembic current

# View logs
docker compose logs -f backend

# Stop services
docker compose -f docker-compose.yml -f docker-compose.postgres.yml down
```

## Default Credentials

The application seeds demo data on first startup:

- **Email**: `admin@example.com`
- **Password**: `admin123`

Additional demo accounts:
- ACC-1001 (with transactions, payments, balance breakdown)
- ACC-1002 (empty state examples)
- ACC-1003 (additional demo account)

## Environment Variables

### Backend Configuration

The backend reads configuration from `.env` (created from `backend/dev.env` on first run):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./app.db` | Database connection string |
| `JWT_SECRET_KEY` | `dev-secret-key-change-in-production` | Secret key for JWT signing |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRY_SECONDS` | `1800` | JWT token expiry (30 minutes) |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:5174` | Allowed CORS origins |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |

**Override database URL:**

```bash
# Local PostgreSQL
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/ccip_balance ./start.sh

# Remote database
DATABASE_URL=postgresql+psycopg://user:pass@db.example.com:5432/ccip ./start.sh
```

### Frontend Configuration

The frontend uses environment variables prefixed with `VITE_`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `/api` | Backend API base URL (relative for same-origin) |
| `BACKEND_PORT` | `9000` | Backend port for Vite dev proxy (dynamic) |

**Note**: In production, the frontend proxies `/api` requests to the backend via nginx. No environment variables are required at runtime.

## Running Tests

### Backend Tests

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Run all tests
python -m pytest

# Run specific test module
python -m pytest tests/test_auth/

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Type checking
python -m mypy app/ --ignore-missing-imports

# Linting
python -m ruff check app/
```

### Frontend Tests

```bash
cd frontend

# Unit tests (run mode)
npm run test

# Unit tests (watch mode)
npm test

# Type checking
npm run type-check

# Linting
npm run lint

# End-to-end tests
npx playwright test

# E2E tests with UI
npx playwright test --ui
```

## Database Migrations

### Create New Migration

```bash
cd backend
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field"

# Create empty migration
alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one revision
alembic upgrade +1

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## API Documentation

The backend provides interactive API documentation:

- **Swagger UI**: http://localhost:9000/docs
- **ReDoc**: http://localhost:9000/redoc
- **OpenAPI JSON**: http://localhost:9000/openapi.json

### Key API Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Current user info
- `POST /api/v1/auth/step-up` - Step-up authentication

#### Accounts
- `GET /api/v1/accounts` - List accounts
- `GET /api/v1/accounts/{id}/overview` - Account overview
- `PUT /api/v1/accounts/selection` - Select account

#### Balance Breakdown
- `GET /api/v1/balance-breakdowns/current` - Current balance breakdown
- `GET /api/v1/balance-breakdowns/{id}/categories/{category_id}` - Category detail

#### Transactions
- `GET /api/v1/transactions` - Transaction history (paginated)

#### Payments
- `GET /api/v1/payments` - Payment history
- `GET /api/v1/payments/{id}` - Payment detail
- `POST /api/v1/payments` - Initiate payment
- `GET /api/v1/payments/guidance` - Payment guidance with direct debit coverage

#### Transfers
- `GET /api/v1/balance-transfers` - Balance transfer history
- `GET /api/v1/balance-transfers/{id}` - Transfer detail
- `POST /api/v1/balance-transfers` - Initiate balance transfer
- `GET /api/v1/money-transfers` - Money transfer history
- `GET /api/v1/money-transfers/{id}` - Transfer detail
- `POST /api/v1/money-transfers` - Initiate money transfer
- `GET /api/v1/payees` - List payees

#### Direct Debits
- `GET /api/v1/direct-debits` - List direct debit mandates
- `POST /api/v1/direct-debits/change-requests` - Initiate mandate change

#### Rewards & Offers
- `GET /api/v1/rewards` - Rewards programme summary
- `GET /api/v1/offers` - Available offers
- `GET /api/v1/instalments` - Instalment plans
- `GET /api/v1/instalments/{plan_id}` - Plan detail

#### Status Tracking
- `GET /api/v1/status-tracker` - Unified tracker view
- `GET /api/v1/status-tracker/{entity_type}/{entity_id}` - Tracker detail
- `POST /api/v1/status-tracker/{entity_type}/{entity_id}/refresh` - Refresh status

#### Support Diagnostics
- `POST /api/v1/support-diagnostics/lookups` - Diagnostic lookup
- `GET /api/v1/support-diagnostics/operational-summary` - Operational metrics

#### Health
- `GET /api/health/live` - Liveness probe
- `GET /api/health/ready` - Readiness probe

## Troubleshooting

### Port Already in Use

The start script automatically detects available ports. If you need specific ports:

```bash
# Backend on port 8000, frontend on port 3000
BACKEND_PORT=8000 FRONTEND_PORT=3000 ./start.sh
```

### Database Locked Error

If you see "database is locked" errors:

```bash
# Stop all services
./stop.sh

# Remove lock files
rm backend/*.db-journal

# Restart
./start.sh
```

### Migration Conflicts

If migrations fail:

```bash
cd backend
source .venv/bin/activate

# Check current revision
alembic current

# View migration history
alembic history

# Downgrade if needed
alembic downgrade -1

# Upgrade again
alembic upgrade head
```

### Frontend Build Errors

If frontend build fails:

```bash
cd frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Rebuild
npm run build
```

## Production Deployment

### Environment Variables (Production)

Override these in production:

```bash
# Backend
export DATABASE_URL="postgresql+psycopg://user:pass@db.example.com:5432/ccip"
export JWT_SECRET_KEY="<secure-random-key>"
export CORS_ORIGINS="https://app.example.com"
export RATE_LIMIT_ENABLED="true"

# Frontend (optional, defaults to /api)
export VITE_API_URL="/api"
```

### Security Checklist

- [ ] Change `JWT_SECRET_KEY` to a secure random value
- [ ] Use PostgreSQL for production database
- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Review and restrict `CORS_ORIGINS`
- [ ] Enable rate limiting
- [ ] Set up database backups
- [ ] Configure monitoring and alerting
- [ ] Review and update default credentials
- [ ] Enable audit logging
- [ ] Configure firewall rules

## License

Proprietary - All Rights Reserved

## Support

For issues and questions, please contact the development team.

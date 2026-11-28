#!/bin/bash
# start.sh - bootstrap and start the backend and frontend locally (SQLite, Docker-free).
# Runs under macOS, Linux and Git Bash. Services run detached; stop them with ./stop.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
PID_FILE="$SCRIPT_DIR/.pids"
LOG_DIR="${TMPDIR:-/tmp}/ccip-balance-breakdown"
mkdir -p "$LOG_DIR"

port_in_use() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$1" -sTCP:LISTEN -t >/dev/null 2>&1
    else
        netstat -an 2>/dev/null | grep -Eq "[:.]$1[[:space:]].*LISTEN"
    fi
}
find_available_port() {
    local port=$1
    while port_in_use "$port"; do
        echo "Port $port in use, trying $((port + 1))..." >&2
        port=$((port + 1))
    done
    echo "$port"
}

# === Prerequisites ===
errors=0
PYTHON=""
for c in python3 python; do
    if "$c" -c 'import sys' >/dev/null 2>&1; then PYTHON=$c; break; fi
done
if [ -z "$PYTHON" ] || ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "Python 3.11+ is required (https://python.org)"
    errors=$((errors + 1))
fi
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "Node.js 20.19+ or 22.12+ and npm are required (https://nodejs.org)"
    errors=$((errors + 1))
fi
if [ "$errors" -gt 0 ]; then exit 1; fi

# === Stop anything a previous run left behind (only the PIDs we recorded) ===
if [ -f "$PID_FILE" ]; then
    while IFS= read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then kill "$pid" 2>/dev/null || true; fi
    done <"$PID_FILE"
    rm -f "$PID_FILE"
fi

# === Backend ===
cd "$SCRIPT_DIR/backend"
[ -d .venv ] || "$PYTHON" -m venv .venv
if [ -f .venv/Scripts/activate ]; then
    # shellcheck disable=SC1091
    source .venv/Scripts/activate
else
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi
[ -f .env ] || cp dev.env .env
echo "Installing backend dependencies..."
pip install . -q || { echo "backend install failed"; exit 1; }
echo "Applying migrations..."
alembic upgrade head || { echo "alembic upgrade failed"; exit 1; }
echo "Seeding (idempotent; only when SEED_ENABLED=true)..."
python -m app.seed || { echo "seed failed"; exit 1; }

BACKEND_PORT=$(find_available_port 9000)
FRONTEND_PORT=$(find_available_port 5173)
[ "$FRONTEND_PORT" != "$BACKEND_PORT" ] || FRONTEND_PORT=$(find_available_port $((FRONTEND_PORT + 1)))
export BACKEND_PORT
# Environment variables override backend/.env, so the CORS allow-list follows the chosen frontend port.
export CORS_ORIGINS="http://localhost:$FRONTEND_PORT,http://127.0.0.1:$FRONTEND_PORT"

nohup python -m uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT" >"$LOG_DIR/backend.log" 2>&1 &
echo "$!" >"$PID_FILE"

# === Frontend ===
cd "$SCRIPT_DIR/frontend"
echo "Installing frontend dependencies..."
npm ci --no-audit --no-fund --loglevel=error || { echo "npm ci failed"; exit 1; }
# The browser calls a relative /api; the Vite proxy reads BACKEND_PORT from this environment.
nohup node ./node_modules/vite/bin/vite.js --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort \
    >"$LOG_DIR/frontend.log" 2>&1 &
echo "$!" >>"$PID_FILE"
cd "$SCRIPT_DIR"

# === Wait for the backend ===
ready=0
for _ in $(seq 1 60); do
    if "$PYTHON" -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:$BACKEND_PORT/health', timeout=2)" >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done
if [ "$ready" -ne 1 ]; then
    echo "WARNING: backend not healthy yet after 60s; check $LOG_DIR/backend.log" >&2
fi

echo ""
echo "=== Services running ==="
echo "  Frontend:  http://localhost:$FRONTEND_PORT"
echo "  Backend:   http://localhost:$BACKEND_PORT  (API under /api/v1, health at /health and /health/ready)"
echo "  API docs:  http://localhost:$BACKEND_PORT/docs  (only while DEBUG=true)"
echo "  Logs:      $LOG_DIR"
echo ""
echo "=== Seeded credentials (synthetic) ==="
echo "  customer: synthetic.customer01 / Prototype!2026"
echo "  customer: synthetic.customer02 / Prototype!2026"
echo "  admin:    synthetic.admin01    / Prototype!2026"
echo ""
echo "Stop with ./stop.sh"

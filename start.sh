#!/bin/bash
# start.sh — Start the full-stack application
set -e
trap 'echo "Shutting down..."; [ -f .pids ] && while IFS= read -r pid; do kill "$pid" 2>/dev/null || true; done < .pids; rm -f .pids; exit 0' SIGINT SIGTERM

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Convert path for native Windows programs under Git Bash
native_path() {
    if command -v cygpath >/dev/null 2>&1; then
        cygpath -m "$1"
    else
        printf '%s' "$1"
    fi
}

# Port detection (lsof on macOS/Linux, netstat under Git Bash on Windows)
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
        echo "Port $port in use, trying $((port+1))..." >&2
        port=$((port+1))
    done
    echo $port
}

# === Prerequisite checks ===
check_prerequisites() {
    local errors=0
    echo "=== Checking prerequisites ==="

    # Probe by running it: under Git Bash `python3` may be the Windows Store stub.
    PYTHON=""
    for c in python3 python; do
        if "$c" -c 'import sys' >/dev/null 2>&1; then
            PYTHON=$c
            break
        fi
    done

    if [ -n "$PYTHON" ]; then
        PYTHON_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
            echo "❌ Python 3.11+ required (found $PYTHON_VERSION)"
            errors=$((errors+1))
        else
            echo "✓ Python $PYTHON_VERSION"
        fi
    else
        echo "❌ Python 3 not found. Install from https://python.org"
        errors=$((errors+1))
    fi

    # Node.js 20.19+/22.12+
    if [ -f "frontend/package.json" ]; then
        if command -v node &>/dev/null; then
            NODE_VERSION=$(node --version | sed 's/v//')
            NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
            NODE_MINOR=$(echo $NODE_VERSION | cut -d. -f2)
            if [ "$NODE_MAJOR" -lt 20 ] || ([ "$NODE_MAJOR" -eq 20 ] && [ "$NODE_MINOR" -lt 19 ]) && [ "$NODE_MAJOR" -lt 22 ]; then
                if [ "$NODE_MAJOR" -ge 22 ] && [ "$NODE_MINOR" -ge 12 ]; then
                    echo "✓ Node.js $NODE_VERSION"
                elif [ "$NODE_MAJOR" -eq 20 ] && [ "$NODE_MINOR" -ge 19 ]; then
                    echo "✓ Node.js $NODE_VERSION"
                else
                    echo "❌ Node.js 20.19+ or 22.12+ required (found $NODE_VERSION)"
                    errors=$((errors+1))
                fi
            else
                echo "✓ Node.js $NODE_VERSION"
            fi
        else
            echo "❌ Node.js not found. Install from https://nodejs.org"
            errors=$((errors+1))
        fi

        if ! command -v npm &>/dev/null; then
            echo "❌ npm not found"
            errors=$((errors+1))
        else
            echo "✓ npm $(npm --version)"
        fi
    fi

    # pip
    if [ -n "$PYTHON" ] && ! "$PYTHON" -m pip --version &>/dev/null; then
        echo "❌ pip not found. Run: $PYTHON -m ensurepip"
        errors=$((errors+1))
    fi

    if [ $errors -gt 0 ]; then
        echo ""
        echo "❌ $errors prerequisite(s) missing. Please install them and retry."
        exit 1
    fi
    echo ""
}

check_prerequisites

# Backend setup
BACKEND_DIR="backend"
echo "=== Setting up backend ==="
cd "$BACKEND_DIR"

# Create venv if missing
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    "$PYTHON" -m venv .venv
fi

# Activate venv (Windows Git Bash vs macOS/Linux)
if [ -f .venv/Scripts/activate ]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Install backend dependencies
echo "Installing backend dependencies..."
pip install . -q || { echo "Backend installation failed"; exit 1; }

# Copy dev.env to .env if missing
if [ ! -f .env ] && [ -f dev.env ]; then
    cp dev.env .env
    echo "Created .env from dev.env"
fi

# Detect available backend port
BACKEND_PORT=$(find_available_port 9000)

# Set up database URL (absolute path, converted for native Windows programs)
DB_PATH="$SCRIPT_DIR/backend/app.db"
export DATABASE_URL="sqlite:///$(native_path "$DB_PATH")"
echo "  Database: $DATABASE_URL"

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head || { echo "Migration failed"; exit 1; }

# Run seed script
echo "Seeding database..."
python -m app.seed || { echo "Seed failed"; exit 1; }

# Start backend
echo "Starting backend on http://127.0.0.1:$BACKEND_PORT"
uvicorn app.main:app --host 127.0.0.1 --port $BACKEND_PORT &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$SCRIPT_DIR/.pids"

cd "$SCRIPT_DIR"

# Frontend setup
FRONTEND_DIR="frontend"
if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/package.json" ]; then
    echo ""
    echo "=== Setting up frontend ==="
    cd "$FRONTEND_DIR"

    # Install frontend dependencies if node_modules missing
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm ci || { echo "Frontend installation failed"; exit 1; }
    fi

    # Detect available frontend port
    FRONTEND_PORT=$(find_available_port 5173)

    # Start frontend (export BACKEND_PORT so vite.config.ts can read it)
    echo "Starting frontend on http://127.0.0.1:$FRONTEND_PORT"
    BACKEND_PORT="$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" >> "$SCRIPT_DIR/.pids"

    cd "$SCRIPT_DIR"
fi

echo ""
echo "=== Services running ==="
echo "  Backend:  http://127.0.0.1:$BACKEND_PORT"
[ -n "$FRONTEND_PORT" ] && echo "  Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "  API Docs: http://127.0.0.1:$BACKEND_PORT/docs"
echo ""
echo "=== Default Credentials ==="
echo "  Login: admin@example.com / admin123"
echo ""
echo "Press Ctrl+C to stop all services"
wait

#!/bin/bash
# backend/run.sh - run the backend on its own (SQLite by default). PORT defaults to 9000.
set -e
cd "$(dirname "$0")"
PYTHON=""
for c in python3 python; do
    if "$c" -c 'import sys' >/dev/null 2>&1; then PYTHON=$c; break; fi
done
[ -n "$PYTHON" ] || { echo "Python 3.11+ is required"; exit 1; }
[ -d .venv ] || "$PYTHON" -m venv .venv
if [ -f .venv/Scripts/activate ]; then
    # shellcheck disable=SC1091
    source .venv/Scripts/activate
else
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi
[ -f .env ] || cp dev.env .env
pip install . -q
alembic upgrade head
python -m app.seed
exec python -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-9000}"

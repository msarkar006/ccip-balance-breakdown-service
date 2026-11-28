#!/bin/bash
# frontend/run.sh - run the frontend dev server on its own.
# The browser calls a relative /api; the Vite proxy forwards it to BACKEND_PORT (default 9000).
set -e
cd "$(dirname "$0")"
command -v npm >/dev/null 2>&1 || { echo "Node.js 20.19+ or 22.12+ and npm are required"; exit 1; }
npm ci --no-audit --no-fund --loglevel=error
export BACKEND_PORT="${BACKEND_PORT:-9000}"
exec node ./node_modules/vite/bin/vite.js --host 127.0.0.1 --port "${PORT:-5173}" --strictPort

#!/bin/sh
# Container provisioning: migrate, seed (idempotent; a no-op unless SEED_ENABLED=true), then run the server.
set -e
alembic upgrade head
python -m app.seed
exec "$@"

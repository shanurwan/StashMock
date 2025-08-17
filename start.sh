#!/usr/bin/env bash
set -euo pipefail

# Wait for DB if needed
if [[ -n "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL=${DATABASE_URL}"
fi

# Run migrations (alembic/env.py will pick DATABASE_URL)
echo "Running alembic upgrade head..."
alembic upgrade head

# Start API
echo "Starting Uvicorn..."
exec python -m uvicorn api.portfolio_service.main:app --host 0.0.0.0 --port 8000

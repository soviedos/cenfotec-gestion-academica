#!/bin/sh
set -e

echo "Running database migrations..."
python -m alembic -c app/infrastructure/database/migrations/alembic.ini upgrade head

echo "Starting application..."
exec "$@"

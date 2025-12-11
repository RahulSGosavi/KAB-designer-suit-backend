#!/bin/bash
set -e

echo "Waiting for database to be ready..."

# Extract connection details from DATABASE_URL if provided, or use individual env vars
if [ -n "$DATABASE_URL" ]; then
    # Parse DATABASE_URL: postgresql://user:password@host:port/dbname
    DB_INFO=$(echo $DATABASE_URL | sed -e 's/^postgresql:\/\///' -e 's/@/ /' -e 's/\// /')
    DB_USER_PASS=$(echo $DB_INFO | cut -d' ' -f1)
    DB_USER=$(echo $DB_USER_PASS | cut -d':' -f1)
    DB_PASS=$(echo $DB_USER_PASS | cut -d':' -f2)
    DB_HOST_PORT=$(echo $DB_INFO | cut -d' ' -f2)
    DB_HOST=$(echo $DB_HOST_PORT | cut -d':' -f1)
    DB_PORT=$(echo $DB_HOST_PORT | cut -d':' -f2)
    DB_NAME=$(echo $DB_INFO | cut -d' ' -f3)
else
    DB_USER=${POSTGRES_USER:-kabuser}
    DB_PASS=${POSTGRES_PASSWORD:-kabpassword}
    DB_HOST=${POSTGRES_HOST:-db}
    DB_PORT=${POSTGRES_PORT:-5432}
    DB_NAME=${POSTGRES_DB:-kabdb}
fi

until PGPASSWORD=$DB_PASS psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

# Initialize schema if it does not exist
if [ -f "src/db/schema.sql" ]; then
  echo "Running initial schema..."
  PGPASSWORD=$DB_PASS psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f src/db/schema.sql 2>&1 | grep -v "already exists" || true
fi

# Run migrations
echo "Running migrations..."
python -m app.db.migrate || echo "Migrations completed with warnings"

# Start server
echo "Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1


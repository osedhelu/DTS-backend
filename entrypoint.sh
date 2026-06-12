#!/usr/bin/env bash
set -euo pipefail

wait_for_db() {
  echo "==> Esperando PostgreSQL..."
  until uv run --no-dev python - <<'PY'
import os
import sys

import psycopg

database_url = os.environ.get("DATABASE_URL", "").strip()
connect_timeout = int(os.environ.get("DB_CONNECT_TIMEOUT", "3"))

try:
    if database_url:
        conn = psycopg.connect(database_url, connect_timeout=connect_timeout)
    else:
        conn = psycopg.connect(
            dbname=os.environ.get("DB_NAME", "dts_delivery"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", "postgres"),
            host=os.environ.get("DB_HOST", "db"),
            port=os.environ.get("DB_PORT", "5432"),
            connect_timeout=connect_timeout,
        )
    conn.close()
except Exception:
    sys.exit(1)
PY
  do
    sleep 2
  done
  echo "==> PostgreSQL listo."
}

enable_postgis() {
  echo "==> Verificando extensión PostGIS..."
  uv run --no-dev python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
print("==> PostGIS OK.")
PY
}

wait_for_db

MEDIA_DIR="${MEDIA_ROOT:-/app/media}"
export MEDIA_ROOT="$MEDIA_DIR"
mkdir -p "$MEDIA_DIR"
echo "==> MEDIA_ROOT=${MEDIA_DIR}"

if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
  enable_postgis
  echo "==> Aplicando migraciones..."
  uv run --no-dev python manage.py migrate --noinput
  echo "==> Verificando tablas críticas (analytics, delivery)..."
  uv run --no-dev python scripts/repair_migration_tables.py
  echo "==> Recolectando archivos estáticos (admin, Swagger)..."
  uv run --no-dev python manage.py collectstatic --noinput --clear
fi

exec "$@"

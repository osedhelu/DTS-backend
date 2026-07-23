#!/usr/bin/env bash
set -euo pipefail

_write_firebase_json() {
  local credentials_path="$1"
  local credentials_json="$2"
  if [[ -z "$credentials_path" || -z "$credentials_json" ]]; then
    return 0
  fi
  local credentials_dir
  credentials_dir="$(dirname "$credentials_path")"
  mkdir -p "$credentials_dir"
  printf '%s' "$credentials_json" >"$credentials_path"
  chmod 600 "$credentials_path"
  echo "==> Credenciales Firebase materializadas en ${credentials_path}"
}

materialize_fcm_credentials() {
  # Compat single-project
  _write_firebase_json \
    "${FCM_CREDENTIALS_PATH:-}" \
    "${FIREBASE_SERVICE_ACCOUNT_JSON:-}"

  # Multi Firebase: customer + driver (ambos dtsdrop-85330)
  _write_firebase_json \
    "${FIREBASE_CUSTOMER_CREDENTIALS_PATH:-}" \
    "${FIREBASE_CUSTOMER_SERVICE_ACCOUNT_JSON:-${FIREBASE_SERVICE_ACCOUNT_JSON:-}}"
  _write_firebase_json \
    "${FIREBASE_DRIVER_CREDENTIALS_PATH:-}" \
    "${FIREBASE_DRIVER_SERVICE_ACCOUNT_JSON:-}"
}

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
materialize_fcm_credentials

# Worker/beat: RUN_MIGRATIONS=false (solo la API migra y collectstatic).
if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
  MEDIA_DIR="${MEDIA_ROOT:-/app/media}"
  export MEDIA_ROOT="$MEDIA_DIR"
  mkdir -p "$MEDIA_DIR"
  echo "==> MEDIA_ROOT=${MEDIA_DIR}"
fi

if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
  enable_postgis
  echo "==> Aplicando migraciones..."
  uv run --no-dev python manage.py migrate --noinput
  echo "==> Verificando tablas críticas (analytics, delivery)..."
  uv run --no-dev python scripts/repair_migration_tables.py
  echo "==> Recolectando archivos estáticos (admin, Swagger)..."
  uv run --no-dev python manage.py collectstatic --noinput --clear
fi

# SERVICE_MODE evita que el worker/beat hereden el CMD Daphne del Dockerfile
# cuando Railway no aplica startCommand de railway.worker.toml.
case "${SERVICE_MODE:-api}" in
  worker)
    echo "==> Iniciando Celery worker (SERVICE_MODE=worker)..."
    export C_FORCE_ROOT="${C_FORCE_ROOT:-1}"
    # Si Railway aún tiene healthcheck HTTP del railway.toml, responder 200 en $PORT
    # para no marcar el deploy como FAILED (Celery no escucha HTTP).
    if [[ -n "${PORT:-}" ]]; then
      uv run python - <<'PY' &
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

port = int(os.environ.get("PORT", "8080"))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_args):
        return

HTTPServer(("0.0.0.0", port), Handler).serve_forever()
PY
      echo "==> Healthcheck shim HTTP en :${PORT}"
    fi
    exec uv run celery -A core worker \
      --loglevel="${CELERY_LOGLEVEL:-info}" \
      --concurrency "${CELERY_CONCURRENCY:-2}"
    ;;
  beat)
    echo "==> Iniciando Celery beat (SERVICE_MODE=beat)..."
    exec uv run celery -A core beat \
      --loglevel="${CELERY_LOGLEVEL:-info}" \
      --schedule "${CELERY_BEAT_SCHEDULE:-/tmp/celerybeat-schedule}"
    ;;
  api|*)
    if [[ "$#" -gt 0 ]]; then
      exec "$@"
    fi
    echo "==> Iniciando Daphne API..."
    exec uv run daphne -b 0.0.0.0 -p "${PORT:-8000}" core.asgi:application
    ;;
esac

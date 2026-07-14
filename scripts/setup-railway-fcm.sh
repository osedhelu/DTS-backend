#!/usr/bin/env bash
# Configura Firebase Admin (customer + driver) en Railway.
#
# Requisitos:
#   - railway CLI autenticado (`railway login`)
#   - JSON de service account por proyecto Firebase
#
# Uso (dual — recomendado):
#   cd backend
#   FIREBASE_CUSTOMER_JSON_FILE=~/Downloads/discorp-adminsdk.json \
#   FIREBASE_DRIVER_JSON_FILE=~/Downloads/dtsdrop-adminsdk.json \
#   ./scripts/setup-railway-fcm.sh
#
# Uso (solo customer / compat):
#   FIREBASE_JSON_FILE=~/Downloads/discorp-adminsdk.json ./scripts/setup-railway-fcm.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CUSTOMER_FILE="${FIREBASE_CUSTOMER_JSON_FILE:-${FIREBASE_JSON_FILE:-}}"
DRIVER_FILE="${FIREBASE_DRIVER_JSON_FILE:-}"

if [[ -z "$CUSTOMER_FILE" || ! -f "$CUSTOMER_FILE" ]]; then
  echo "Define FIREBASE_CUSTOMER_JSON_FILE (o FIREBASE_JSON_FILE) con el JSON discorp." >&2
  exit 1
fi

CUSTOMER_PATH="/app/secrets/firebase-customer.json"
DRIVER_PATH="/app/secrets/firebase-driver.json"
LEGACY_PATH="/app/secrets/firebase-service-account.json"

CUSTOMER_JSON="$(tr -d '\n' <"$CUSTOMER_FILE")"

set_vars=(
  --set "FIREBASE_CUSTOMER_CREDENTIALS_PATH=${CUSTOMER_PATH}"
  --set "FIREBASE_CUSTOMER_SERVICE_ACCOUNT_JSON=${CUSTOMER_JSON}"
  --set "FCM_CREDENTIALS_PATH=${LEGACY_PATH}"
  --set "FIREBASE_SERVICE_ACCOUNT_JSON=${CUSTOMER_JSON}"
)

if [[ -n "$DRIVER_FILE" ]]; then
  if [[ ! -f "$DRIVER_FILE" ]]; then
    echo "FIREBASE_DRIVER_JSON_FILE no existe: ${DRIVER_FILE}" >&2
    exit 1
  fi
  DRIVER_JSON="$(tr -d '\n' <"$DRIVER_FILE")"
  set_vars+=(
    --set "FIREBASE_DRIVER_CREDENTIALS_PATH=${DRIVER_PATH}"
    --set "FIREBASE_DRIVER_SERVICE_ACCOUNT_JSON=${DRIVER_JSON}"
  )
else
  echo "WARN: sin FIREBASE_DRIVER_JSON_FILE — solo customer/compat. Google/Apple driver y FCM conductor no funcionarán hasta añadirlo."
fi

for SERVICE in DTS-backend DTS-backend-worker; do
  echo "==> Configurando ${SERVICE}..."
  railway variables --service "$SERVICE" "${set_vars[@]}"
done

echo "==> Listo. Redespliega ambos servicios:"
echo "    railway redeploy --service DTS-backend"
echo "    railway redeploy --service DTS-backend-worker"

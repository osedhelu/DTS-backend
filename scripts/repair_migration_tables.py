#!/usr/bin/env python
"""
Repara migraciones marcadas como aplicadas pero sin tablas en PostgreSQL.

Útil tras reset de volumen, restores parciales o despliegues inconsistentes.
Se ejecuta automáticamente en el entrypoint Docker antes de arrancar Gunicorn.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import django
from django.core.management import call_command
from django.db import connection

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# app_label -> tablas críticas que deben existir si la migración inicial está aplicada
APP_CRITICAL_TABLES: dict[str, list[str]] = {
    "analytics": [
        "analytics_daily_sales_report",
        "analytics_driver_commission",
    ],
    "delivery": [
        "delivery_deliverytracking",
        "delivery_trackingpoint",
    ],
}


def _table_exists(table_name: str) -> bool:
    return table_name in connection.introspection.table_names()


def _migration_applied(app_label: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM django_migrations WHERE app = %s LIMIT 1",
            [app_label],
        )
        return cursor.fetchone() is not None


def _ensure_postgis() -> None:
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")


def repair() -> None:
    _ensure_postgis()
    repaired: list[str] = []

    for app_label, tables in APP_CRITICAL_TABLES.items():
        if not _migration_applied(app_label):
            continue

        missing = [table for table in tables if not _table_exists(table)]
        if not missing:
            continue

        print(
            f"==> Reparando {app_label}: migración aplicada pero faltan tablas {missing}",
            flush=True,
        )
        call_command("migrate", app_label, "zero", fake=True, verbosity=1)
        call_command("migrate", app_label, verbosity=1)
        repaired.append(app_label)

    if repaired:
        print(f"==> Migraciones reparadas: {', '.join(repaired)}", flush=True)
    else:
        print("==> Tablas críticas OK (sin reparación de migraciones)", flush=True)


if __name__ == "__main__":
    repair()

"""Inicialización multi-proyecto de firebase-admin (customer + driver)."""

from __future__ import annotations

import json
from typing import Any

from django.conf import settings

from features.notifications.domain.exceptions import FCMNotConfiguredError

FIREBASE_APP_CUSTOMER = "customer"
FIREBASE_APP_DRIVER = "driver"


def _credentials_path_for_app(app_name: str) -> str | None:
    if app_name == FIREBASE_APP_DRIVER:
        return (
            getattr(settings, "FIREBASE_DRIVER_CREDENTIALS_PATH", None)
            or getattr(settings, "FCM_CREDENTIALS_PATH", None)
        )
    return (
        getattr(settings, "FIREBASE_CUSTOMER_CREDENTIALS_PATH", None)
        or getattr(settings, "FCM_CREDENTIALS_PATH", None)
    )


def _service_account_json_for_app(app_name: str) -> str | None:
    if app_name == FIREBASE_APP_DRIVER:
        return getattr(settings, "FIREBASE_DRIVER_SERVICE_ACCOUNT_JSON", None)
    return (
        getattr(settings, "FIREBASE_CUSTOMER_SERVICE_ACCOUNT_JSON", None)
        or getattr(settings, "FIREBASE_SERVICE_ACCOUNT_JSON", None)
    )


def _certificate_source(app_name: str) -> str | dict[str, Any]:
    """Prefer JSON en env (Railway); fallback a path materializado por entrypoint."""
    raw = (_service_account_json_for_app(app_name) or "").strip()
    if raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FCMNotConfiguredError(
                f"FIREBASE_*_SERVICE_ACCOUNT_JSON inválido para app '{app_name}'"
            ) from exc
        if not isinstance(data, dict):
            raise FCMNotConfiguredError(
                f"FIREBASE_*_SERVICE_ACCOUNT_JSON debe ser un objeto JSON "
                f"para app '{app_name}'"
            )
        return data

    path = _credentials_path_for_app(app_name)
    if path:
        return path

    raise FCMNotConfiguredError(
        f"Credenciales Firebase no configuradas para app '{app_name}'"
    )


def ensure_firebase_app(app_name: str = FIREBASE_APP_CUSTOMER):
    """Devuelve la app firebase-admin nombrada, inicializándola si hace falta."""
    import firebase_admin
    from firebase_admin import credentials

    try:
        return firebase_admin.get_app(app_name)
    except ValueError:
        pass

    source = _certificate_source(app_name)
    try:
        cred = credentials.Certificate(source)
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise FCMNotConfiguredError(
            f"No se pudieron cargar credenciales Firebase para app '{app_name}'"
        ) from exc

    return firebase_admin.initialize_app(cred, name=app_name)


def firebase_app_for_role(role: str) -> str:
    from features.accounts.domain.entities import UserRole

    if role == UserRole.DRIVER:
        return FIREBASE_APP_DRIVER
    return FIREBASE_APP_CUSTOMER

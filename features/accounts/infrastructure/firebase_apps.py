"""Inicialización multi-proyecto de firebase-admin (customer + driver)."""

from __future__ import annotations

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


def ensure_firebase_app(app_name: str = FIREBASE_APP_CUSTOMER):
    """Devuelve la app firebase-admin nombrada, inicializándola si hace falta."""
    import firebase_admin
    from firebase_admin import credentials

    try:
        return firebase_admin.get_app(app_name)
    except ValueError:
        pass

    path = _credentials_path_for_app(app_name)
    if not path:
        raise FCMNotConfiguredError(
            f"Credenciales Firebase no configuradas para app '{app_name}'"
        )

    cred = credentials.Certificate(path)
    return firebase_admin.initialize_app(cred, name=app_name)


def firebase_app_for_role(role: str) -> str:
    from features.accounts.domain.entities import UserRole

    if role == UserRole.DRIVER:
        return FIREBASE_APP_DRIVER
    return FIREBASE_APP_CUSTOMER

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings

from features.accounts.infrastructure.firebase_apps import (
    FIREBASE_APP_CUSTOMER,
    firebase_app_for_role,
)
from features.notifications.domain.exceptions import FCMNotConfiguredError, FCMSendError


@dataclass(frozen=True, slots=True)
class PushPayload:
    token: str
    title: str
    body: str
    data: dict[str, str] | None = None


class FCMClient:
    """Cliente FCM vía firebase-admin (app nombrada por proyecto)."""

    def __init__(
        self,
        credentials_path: str | None = None,
        *,
        app_name: str = FIREBASE_APP_CUSTOMER,
    ) -> None:
        self._credentials_path = credentials_path
        self._app_name = app_name
        self._app = None
        self._initialized = False

    def send(
        self,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> str:
        payload = PushPayload(token=token, title=title, body=body, data=data)
        return self.send_payload(payload)

    def send_payload(self, payload: PushPayload) -> str:
        app = self._ensure_initialized()

        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(
                title=payload.title,
                body=payload.body,
            ),
            token=payload.token,
            data=payload.data or {},
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default",
                    channel_id=(
                        "order_chat"
                        if (payload.data or {}).get("type") == "chat_message"
                        else "order_updates"
                    ),
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default"),
                ),
            ),
        )

        try:
            return messaging.send(message, app=app)
        except Exception as exc:
            raise FCMSendError(f"No se pudo enviar push FCM: {exc}") from exc

    def _ensure_initialized(self):
        if self._initialized:
            return self._app

        from features.accounts.infrastructure.firebase_apps import ensure_firebase_app

        # Paths/JSON se resuelven en ensure_firebase_app (env Railway + path).
        self._app = ensure_firebase_app(self._app_name)
        self._initialized = True
        return self._app


def get_fcm_client(**overrides: Any) -> FCMClient:
    role = overrides.get("role")
    app_name = overrides.get("app_name")
    if app_name is None and role is not None:
        app_name = firebase_app_for_role(str(role))
    if app_name is None:
        app_name = FIREBASE_APP_CUSTOMER

    credentials_path = overrides.get("credentials_path")
    if credentials_path is None:
        if app_name == "driver":
            credentials_path = (
                getattr(settings, "FIREBASE_DRIVER_CREDENTIALS_PATH", None)
                or getattr(settings, "FCM_CREDENTIALS_PATH", None)
            )
        else:
            credentials_path = (
                getattr(settings, "FIREBASE_CUSTOMER_CREDENTIALS_PATH", None)
                or getattr(settings, "FCM_CREDENTIALS_PATH", None)
            )

    return FCMClient(credentials_path=credentials_path, app_name=app_name)

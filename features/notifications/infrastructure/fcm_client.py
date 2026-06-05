from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings

from features.notifications.domain.exceptions import FCMNotConfiguredError, FCMSendError


@dataclass(frozen=True, slots=True)
class PushPayload:
    token: str
    title: str
    body: str
    data: dict[str, str] | None = None


class FCMClient:
    """Cliente FCM vía firebase-admin."""

    def __init__(self, credentials_path: str | None = None) -> None:
        self._credentials_path = credentials_path
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
        self._ensure_initialized()

        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(
                title=payload.title,
                body=payload.body,
            ),
            token=payload.token,
            data=payload.data or {},
        )

        try:
            return messaging.send(message)
        except Exception as exc:
            raise FCMSendError(f"No se pudo enviar push FCM: {exc}") from exc

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        if not self._credentials_path:
            raise FCMNotConfiguredError(
                "FCM_CREDENTIALS_PATH no está configurado en settings"
            )

        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            cred = credentials.Certificate(self._credentials_path)
            firebase_admin.initialize_app(cred)

        self._initialized = True


def get_fcm_client(**overrides: Any) -> FCMClient:
    credentials_path = overrides.get(
        "credentials_path",
        getattr(settings, "FCM_CREDENTIALS_PATH", None),
    )
    return FCMClient(credentials_path=credentials_path)

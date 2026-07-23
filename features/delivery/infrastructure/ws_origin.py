"""Validadores WebSocket compatibles con clientes nativos (Flutter)."""

from __future__ import annotations

from urllib.parse import urlparse

from channels.security.websocket import OriginValidator, WebsocketDenier
from django.conf import settings


class NativeClientOriginValidator:
    """Como AllowedHostsOriginValidator, pero permite conexiones sin Origin.

    Flutter (iOS/Android) suele no enviar ``Origin`` en WebSocket; el validador
    estándar de Channels lo rechaza con 403 aunque el JWT sea válido.
    Si hay Origin, se valida contra ``ALLOWED_HOSTS``.
    """

    def __init__(self, application):
        allowed_hosts = list(settings.ALLOWED_HOSTS)
        if settings.DEBUG and not allowed_hosts:
            allowed_hosts = ["localhost", "127.0.0.1", "[::1]"]
        self._strict = OriginValidator(application, allowed_hosts)
        self._application = application

    async def __call__(self, scope, receive, send):
        if scope["type"] != "websocket":
            raise ValueError(
                "NativeClientOriginValidator solo aplica a conexiones WebSocket"
            )

        has_origin = any(
            name == b"origin" for name, _value in scope.get("headers", [])
        )
        if not has_origin:
            return await self._application(scope, receive, send)
        return await self._strict(scope, receive, send)

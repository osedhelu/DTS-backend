"""Autenticación JWT para WebSockets (Flutter Bearer / query token)."""

from __future__ import annotations

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _user_from_token(raw_token: str):
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    from rest_framework_simplejwt.tokens import AccessToken

    from features.accounts.infrastructure.models import CustomUser

    try:
        access = AccessToken(raw_token)
        user_id = access.get("user_id")
        if user_id is None:
            return AnonymousUser()
        return CustomUser.objects.get(pk=user_id)
    except (InvalidToken, TokenError, CustomUser.DoesNotExist, KeyError):
        return AnonymousUser()


def _extract_token(scope: dict) -> str | None:
    query = parse_qs(scope.get("query_string", b"").decode())
    token_values = query.get("token") or query.get("access_token")
    if token_values and token_values[0]:
        return token_values[0]

    headers = dict(scope.get("headers") or [])
    auth = headers.get(b"authorization", b"").decode()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


class JwtAuthMiddleware(BaseMiddleware):
    """Rellena `scope['user']` desde JWT (?token= o Authorization: Bearer)."""

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            token = _extract_token(scope)
            scope["user"] = (
                await _user_from_token(token) if token else AnonymousUser()
            )
        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(inner)

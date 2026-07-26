"""Tests del validador Origin compatible con Flutter nativo."""

from unittest.mock import AsyncMock

import pytest

from features.delivery.infrastructure.ws_origin import NativeClientOriginValidator


@pytest.mark.asyncio
async def test_allows_websocket_without_origin_header(settings):
    settings.ALLOWED_HOSTS = ["dts-backend-production-c84e.up.railway.app"]
    inner = AsyncMock(return_value="ok")
    validator = NativeClientOriginValidator(inner)

    scope = {"type": "websocket", "headers": []}
    result = await validator(scope, AsyncMock(), AsyncMock())

    assert result == "ok"
    inner.assert_awaited_once()


@pytest.mark.asyncio
async def test_allows_websocket_with_allowed_origin(settings):
    settings.ALLOWED_HOSTS = ["dts-backend-production-c84e.up.railway.app"]
    inner = AsyncMock(return_value="ok")
    validator = NativeClientOriginValidator(inner)

    scope = {
        "type": "websocket",
        "headers": [
            (
                b"origin",
                b"https://dts-backend-production-c84e.up.railway.app",
            )
        ],
    }
    result = await validator(scope, AsyncMock(), AsyncMock())

    assert result == "ok"
    inner.assert_awaited_once()


@pytest.mark.asyncio
async def test_denies_websocket_with_disallowed_origin(settings, monkeypatch):
    settings.ALLOWED_HOSTS = ["dts-backend-production-c84e.up.railway.app"]

    class ImmediateDenier:
        """Sustituye WebsocketDenier para no colgarse en Redis/ASGI."""

        async def __call__(self, scope, receive, send):
            await send({"type": "websocket.close", "code": 1000})

    monkeypatch.setattr(
        "channels.security.websocket.WebsocketDenier",
        ImmediateDenier,
    )

    inner = AsyncMock(return_value="ok")
    validator = NativeClientOriginValidator(inner)

    send = AsyncMock()
    scope = {
        "type": "websocket",
        "headers": [(b"origin", b"https://evil.example.com")],
    }
    await validator(scope, AsyncMock(), send)

    inner.assert_not_awaited()
    send.assert_awaited()
    assert send.await_args.args[0]["type"] == "websocket.close"

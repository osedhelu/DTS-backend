"""Tests del validador Origin compatible con Flutter nativo."""

from unittest.mock import AsyncMock, MagicMock

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
async def test_denies_websocket_with_disallowed_origin(settings):
    settings.ALLOWED_HOSTS = ["dts-backend-production-c84e.up.railway.app"]
    inner = AsyncMock(return_value="ok")
    validator = NativeClientOriginValidator(inner)

    send = AsyncMock()
    scope = {
        "type": "websocket",
        "headers": [(b"origin", b"https://evil.example.com")],
    }
    await validator(scope, AsyncMock(), send)

    inner.assert_not_awaited()
    # WebsocketDenier cierra la conexión
    assert send.await_count >= 1

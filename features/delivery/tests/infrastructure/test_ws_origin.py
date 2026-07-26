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
    # Sin channel layer: WebsocketDenier no se queda esperando Redis forever.
    monkeypatch.setattr(
        "channels.consumer.get_channel_layer",
        lambda *args, **kwargs: None,
    )
    inner = AsyncMock(return_value="ok")
    validator = NativeClientOriginValidator(inner)

    send = AsyncMock()
    receive = AsyncMock(side_effect=[{"type": "websocket.connect"}])
    scope = {
        "type": "websocket",
        "headers": [(b"origin", b"https://evil.example.com")],
    }
    await validator(scope, receive, send)

    inner.assert_not_awaited()
    # WebsocketDenier cierra la conexión tras el handshake
    assert send.await_count >= 1

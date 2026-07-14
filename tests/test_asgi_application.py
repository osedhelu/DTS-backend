"""T5.1.1 — Django Channels + channels-redis ASGI."""

from channels.routing import ProtocolTypeRouter
from django.conf import settings


def test_asgi_application_loads():
    from core.asgi import application

    assert settings.ASGI_APPLICATION == "core.asgi.application"
    assert "daphne" in settings.INSTALLED_APPS
    assert "channels" in settings.INSTALLED_APPS
    assert "default" in settings.CHANNEL_LAYERS

    backend = settings.CHANNEL_LAYERS["default"]["BACKEND"]
    assert backend in {
        "channels.layers.InMemoryChannelLayer",
        "channels_redis.core.RedisChannelLayer",
    }

    assert isinstance(application, ProtocolTypeRouter)
    assert "http" in application.application_mapping
    assert "websocket" in application.application_mapping

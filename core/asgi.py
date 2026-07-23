"""
ASGI entrypoint con Django Channels — T5.1.1 / T5.1.2.

HTTP sigue en Django; WebSocket usa JWT + TrackingConsumer.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Django debe inicializarse antes de importar routing/consumers.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from core.routing import websocket_urlpatterns  # noqa: E402
from features.delivery.infrastructure.ws_auth import JwtAuthMiddlewareStack  # noqa: E402
from features.delivery.infrastructure.ws_origin import (  # noqa: E402
    NativeClientOriginValidator,
)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": NativeClientOriginValidator(
            JwtAuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)

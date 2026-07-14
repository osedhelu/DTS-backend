"""Rutas WebSocket ASGI — T5.1.1+."""

from django.urls import path

from features.delivery.infrastructure.consumers import TrackingConsumer

websocket_urlpatterns = [
    path(
        "ws/orders/<int:order_id>/tracking/",
        TrackingConsumer.as_asgi(),
        name="ws-order-tracking",
    ),
]

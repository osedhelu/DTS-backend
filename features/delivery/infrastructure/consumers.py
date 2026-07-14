"""WebSocket consumers de tracking — T5.1.2 / T5.2.1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from features.delivery.domain.exceptions import (
    DomainValidationError,
    InvalidOrderStatusForTrackingError,
    ServiceOrderNotTrackableError,
    UnauthorizedDriverError,
)
from features.orders.domain.exceptions import OrderNotFoundError


@dataclass(frozen=True, slots=True)
class TrackingOrderAccess:
    order_id: int
    customer_id: int
    driver_id: int | None


def get_tracking_order_access(order_id: int) -> TrackingOrderAccess | None:
    """Carga IDs mínimos del pedido para autorizar el room WS."""
    from features.orders.infrastructure.models import Order

    try:
        order = Order.objects.only("id", "customer_id", "driver_id").get(pk=order_id)
    except Order.DoesNotExist:
        return None
    return TrackingOrderAccess(
        order_id=order.id,
        customer_id=order.customer_id,
        driver_id=order.driver_id,
    )


def user_can_join_tracking(user, order: TrackingOrderAccess) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if order.customer_id == user.id:
        return True
    if order.driver_id is not None and order.driver_id == user.id:
        return True
    return False


def tracking_room_name(order_id: int) -> str:
    return f"tracking_{order_id}"


def _parse_recorded_at(raw: Any) -> datetime:
    if raw is None:
        return timezone.now()
    if isinstance(raw, datetime):
        when = raw
    else:
        when = parse_datetime(str(raw))
        if when is None:
            raise DomainValidationError("recorded_at inválido")
    if timezone.is_naive(when):
        when = timezone.make_aware(when, timezone.get_current_timezone())
    return when


def record_driver_location_from_ws(
    *,
    order_id: int,
    driver_id: int,
    latitude: float,
    longitude: float,
    recorded_at: Any = None,
) -> dict[str, Any]:
    """Persiste el punto GPS (mismo use case que POST REST) y arma el payload WS."""
    from features.delivery.application.dto import RecordLocationDTO
    from features.delivery.application.use_cases.record_location import RecordLocationUseCase
    from features.delivery.infrastructure.repositories import DjangoDeliveryTrackingRepository
    from features.orders.infrastructure.repositories import DjangoOrderRepository

    when = _parse_recorded_at(recorded_at)
    tracking = RecordLocationUseCase(
        DjangoOrderRepository(),
        DjangoDeliveryTrackingRepository(),
    ).execute(
        RecordLocationDTO(
            order_id=order_id,
            driver_id=driver_id,
            latitude=latitude,
            longitude=longitude,
            recorded_at=when,
        )
    )
    last = tracking.points[-1] if tracking.points else None
    return {
        "type": "location",
        "order_id": order_id,
        "latitude": latitude,
        "longitude": longitude,
        "recorded_at": (last.recorded_at if last else when).isoformat(),
        "sequence": last.sequence if last else None,
    }


class TrackingConsumer(AsyncJsonWebsocketConsumer):
    """
    Cliente/conductor se suscriben al room del pedido.

    Auth: JWT en `?token=` (ver JwtAuthMiddleware).
    Driver → `{"type":"location","latitude":…,"longitude":…}` → broadcast al room.
    """

    room_group_name: str | None = None
    order_id: int | None = None
    user_id: int | None = None
    is_order_driver: bool = False

    async def connect(self):
        order_id = int(self.scope["url_route"]["kwargs"]["order_id"])
        user = self.scope.get("user")

        if user is None or not getattr(user, "is_authenticated", False):
            await self.close(code=4001)
            return

        order = await database_sync_to_async(get_tracking_order_access)(order_id)
        if order is None:
            await self.close(code=4004)
            return

        if not user_can_join_tracking(user, order):
            await self.close(code=4003)
            return

        self.order_id = order_id
        self.user_id = user.id
        self.is_order_driver = order.driver_id is not None and order.driver_id == user.id
        self.room_group_name = tracking_room_name(order_id)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            await self.send_json({"type": "error", "detail": "JSON inválido"})
            return

        msg_type = content.get("type")
        if msg_type != "location":
            await self.send_json(
                {"type": "error", "detail": "Tipo de mensaje no soportado"}
            )
            return

        if not self.is_order_driver:
            await self.send_json(
                {
                    "type": "error",
                    "detail": "Solo el conductor asignado puede enviar ubicación",
                }
            )
            return

        try:
            latitude = float(content["latitude"])
            longitude = float(content["longitude"])
        except (KeyError, TypeError, ValueError):
            await self.send_json(
                {"type": "error", "detail": "latitude/longitude inválidos"}
            )
            return

        try:
            payload = await database_sync_to_async(record_driver_location_from_ws)(
                order_id=self.order_id,
                driver_id=self.user_id,
                latitude=latitude,
                longitude=longitude,
                recorded_at=content.get("recorded_at"),
            )
        except (
            OrderNotFoundError,
            UnauthorizedDriverError,
            InvalidOrderStatusForTrackingError,
            ServiceOrderNotTrackableError,
            DomainValidationError,
        ) as exc:
            await self.send_json({"type": "error", "detail": str(exc)})
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "tracking.location",
                "payload": payload,
            },
        )

    async def tracking_location(self, event):
        await self.send_json(event["payload"])

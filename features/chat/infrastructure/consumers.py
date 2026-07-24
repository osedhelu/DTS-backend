"""WebSocket consumer de chat por pedido."""

from __future__ import annotations

from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from features.chat.domain.exceptions import (
    DomainValidationError,
    EmptyChatMessageError,
    UnauthorizedChatAccessError,
)
from features.orders.domain.exceptions import OrderNotFoundError


def chat_room_name(order_id: int) -> str:
    return f"chat_{order_id}"


def _user_can_join(user, order_id: int) -> bool:
    from features.chat.application.participants import user_is_chat_participant
    from features.orders.infrastructure.models import Order

    if not getattr(user, "is_authenticated", False):
        return False
    try:
        order = Order.objects.select_related("store").get(pk=order_id)
    except Order.DoesNotExist:
        return False
    return user_is_chat_participant(order, user.id)


def _send_message_sync(order_id: int, sender_id: int, body: str) -> dict[str, Any]:
    from features.chat.application.use_cases.send_order_message import SendOrderMessageUseCase

    msg = SendOrderMessageUseCase().execute(order_id, sender_id, body)
    return {
        "type": "message",
        "id": msg.id,
        "order_id": msg.order_id,
        "sender_id": msg.sender_id,
        "sender_role": msg.sender_role,
        "body": msg.body,
        "created_at": msg.created_at.isoformat(),
    }


class OrderChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.order_id = int(self.scope["url_route"]["kwargs"]["order_id"])
        user = self.scope.get("user")
        allowed = await database_sync_to_async(_user_can_join)(user, self.order_id)
        if not allowed:
            await self.close()
            return

        self.room = chat_room_name(self.order_id)
        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "room"):
            await self.channel_layer.group_discard(self.room, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # REST es source of truth; WS puede crear mensaje (web) sin duplicar fan-out
        # porque SendOrderMessageUseCase ya hace group_send.
        if content.get("type") == "echo":
            await self.send_json({"type": "pong"})
            return
        if content.get("type") != "message":
            await self.send_json({"type": "error", "detail": "Tipo no soportado"})
            return

        user = self.scope.get("user")
        try:
            await database_sync_to_async(_send_message_sync)(
                self.order_id,
                user.id,
                content.get("body", ""),
            )
        except (
            OrderNotFoundError,
            UnauthorizedChatAccessError,
            EmptyChatMessageError,
            DomainValidationError,
        ) as exc:
            await self.send_json({"type": "error", "detail": str(exc)})
            return
        # Broadcast ya lo hace el use case; no group_send otra vez.

    async def chat_message(self, event):
        await self.send_json(event["payload"])

    async def order_status(self, event):
        await self.send_json(event["payload"])

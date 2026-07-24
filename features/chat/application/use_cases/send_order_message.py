from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from features.chat.application.dto import ChatMessageDTO
from features.chat.application.participants import (
    assert_chat_participant,
    other_chat_participant_ids,
)
from features.chat.domain.exceptions import EmptyChatMessageError
from features.chat.infrastructure.models import OrderChatMessage
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.infrastructure.models import Order as OrderModel


def _enqueue_chat_push(
    order_id: int,
    recipient_id: int,
    preview: str,
    sender_role: str,
) -> None:
    from features.notifications.infrastructure.tasks import notify_chat_message_task

    notify_chat_message_task.delay(
        order_id,
        recipient_id,
        preview,
        sender_role,
    )


def _broadcast_chat_message(order_id: int, payload: dict) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_{order_id}",
        {"type": "chat.message", "payload": payload},
    )


class SendOrderMessageUseCase:
    def execute(self, order_id: int, sender_id: int, body: str) -> ChatMessageDTO:
        text = (body or "").strip()
        if not text:
            raise EmptyChatMessageError("El mensaje no puede estar vacío")

        try:
            order = OrderModel.objects.select_related("store").get(pk=order_id)
        except OrderModel.DoesNotExist as exc:
            raise OrderNotFoundError(f"Pedido {order_id} no encontrado") from exc

        assert_chat_participant(order, sender_id)

        msg = OrderChatMessage.objects.create(
            order_id=order_id,
            sender_id=sender_id,
            body=text[:2000],
        )
        msg = OrderChatMessage.objects.select_related("sender").get(pk=msg.pk)
        dto = ChatMessageDTO(
            id=msg.id,
            order_id=msg.order_id,
            sender_id=msg.sender_id,
            sender_role=getattr(msg.sender, "role", ""),
            body=msg.body,
            created_at=msg.created_at,
        )

        payload = {
            "type": "message",
            "id": dto.id,
            "order_id": dto.order_id,
            "sender_id": dto.sender_id,
            "sender_role": dto.sender_role,
            "body": dto.body,
            "created_at": dto.created_at.isoformat(),
        }
        _broadcast_chat_message(order_id, payload)

        for recipient_id in other_chat_participant_ids(order, sender_id):
            _enqueue_chat_push(
                order_id=order_id,
                recipient_id=recipient_id,
                preview=dto.body,
                sender_role=dto.sender_role,
            )

        return dto

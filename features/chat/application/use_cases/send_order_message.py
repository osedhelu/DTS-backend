from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.media_urls import build_public_media_url
from features.chat.application.dto import ChatMessageDTO
from features.chat.application.participants import (
    assert_chat_open,
    assert_chat_participant,
    other_chat_participant_ids,
)
from features.chat.domain.exceptions import EmptyChatMessageError
from features.chat.infrastructure.models import ChatMessageType, OrderChatMessage
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.infrastructure.models import Order as OrderModel


def _image_url(msg: OrderChatMessage) -> str:
    if not msg.image:
        return ""
    try:
        return build_public_media_url(msg.image.url)
    except (ValueError, OSError):
        return ""


def message_to_dto(msg: OrderChatMessage) -> ChatMessageDTO:
    return ChatMessageDTO(
        id=msg.id,
        order_id=msg.order_id,
        sender_id=msg.sender_id,
        sender_role=getattr(msg.sender, "role", ""),
        body=msg.body,
        created_at=msg.created_at,
        message_type=msg.message_type,
        image_url=_image_url(msg),
    )


def message_to_ws_payload(dto: ChatMessageDTO) -> dict:
    return {
        "type": "message",
        "id": dto.id,
        "order_id": dto.order_id,
        "sender_id": dto.sender_id,
        "sender_role": dto.sender_role,
        "body": dto.body,
        "message_type": dto.message_type,
        "image_url": dto.image_url,
        "created_at": dto.created_at.isoformat(),
    }


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


def broadcast_chat_message(order_id: int, payload: dict) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_{order_id}",
        {"type": "chat.message", "payload": payload},
    )


def broadcast_chat_closed(order_id: int) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_{order_id}",
        {
            "type": "chat.message",
            "payload": {"type": "chat.closed", "order_id": order_id, "chat_closed": True},
        },
    )


class SendOrderMessageUseCase:
    def execute(
        self,
        order_id: int,
        sender_id: int,
        body: str,
        *,
        allow_when_closed: bool = False,
        message_type: str = ChatMessageType.TEXT,
        image_name: str | None = None,
    ) -> ChatMessageDTO:
        text = (body or "").strip()
        is_image = message_type == ChatMessageType.IMAGE
        if not is_image and not text:
            raise EmptyChatMessageError("El mensaje no puede estar vacío")
        if is_image and not image_name:
            raise EmptyChatMessageError("La imagen de chat es obligatoria")

        try:
            order = OrderModel.objects.select_related("store").get(pk=order_id)
        except OrderModel.DoesNotExist as exc:
            raise OrderNotFoundError(f"Pedido {order_id} no encontrado") from exc

        assert_chat_participant(order, sender_id)
        if not allow_when_closed:
            assert_chat_open(order)

        msg = OrderChatMessage(
            order_id=order_id,
            sender_id=sender_id,
            body=(text or ("Pedido entregado" if is_image else ""))[:2000],
            message_type=message_type,
        )
        if image_name:
            msg.image.name = image_name
        msg.save()

        msg = OrderChatMessage.objects.select_related("sender").get(pk=msg.pk)
        dto = message_to_dto(msg)
        payload = message_to_ws_payload(dto)
        broadcast_chat_message(order_id, payload)

        preview = dto.body if dto.body else "Foto de entrega"
        for recipient_id in other_chat_participant_ids(order, sender_id):
            _enqueue_chat_push(
                order_id=order_id,
                recipient_id=recipient_id,
                preview=preview,
                sender_role=dto.sender_role,
            )

        return dto

from features.chat.application.dto import ChatMessageDTO
from features.chat.domain.exceptions import EmptyChatMessageError, UnauthorizedChatAccessError
from features.chat.infrastructure.models import OrderChatMessage
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.infrastructure.models import Order as OrderModel


def _assert_participant(order: OrderModel, user_id: int) -> None:
    if order.customer_id == user_id:
        return
    if order.driver_id is not None and order.driver_id == user_id:
        return
    raise UnauthorizedChatAccessError("No tienes acceso al chat de este pedido")


class SendOrderMessageUseCase:
    def execute(self, order_id: int, sender_id: int, body: str) -> ChatMessageDTO:
        text = (body or "").strip()
        if not text:
            raise EmptyChatMessageError("El mensaje no puede estar vacío")

        try:
            order = OrderModel.objects.select_related().get(pk=order_id)
        except OrderModel.DoesNotExist as exc:
            raise OrderNotFoundError(f"Pedido {order_id} no encontrado") from exc

        _assert_participant(order, sender_id)

        msg = OrderChatMessage.objects.create(
            order_id=order_id,
            sender_id=sender_id,
            body=text[:2000],
        )
        msg = OrderChatMessage.objects.select_related("sender").get(pk=msg.pk)
        return ChatMessageDTO(
            id=msg.id,
            order_id=msg.order_id,
            sender_id=msg.sender_id,
            sender_role=getattr(msg.sender, "role", ""),
            body=msg.body,
            created_at=msg.created_at,
        )

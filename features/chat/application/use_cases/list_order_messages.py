from features.chat.application.dto import ChatMessageDTO
from features.chat.domain.exceptions import UnauthorizedChatAccessError
from features.chat.infrastructure.models import OrderChatMessage
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.infrastructure.models import Order as OrderModel


def _assert_participant(order: OrderModel, user_id: int) -> None:
    if order.customer_id == user_id:
        return
    if order.driver_id is not None and order.driver_id == user_id:
        return
    raise UnauthorizedChatAccessError("No tienes acceso al chat de este pedido")


def _to_dto(msg: OrderChatMessage) -> ChatMessageDTO:
    return ChatMessageDTO(
        id=msg.id,
        order_id=msg.order_id,
        sender_id=msg.sender_id,
        sender_role=getattr(msg.sender, "role", ""),
        body=msg.body,
        created_at=msg.created_at,
    )


class ListOrderMessagesUseCase:
    def execute(self, order_id: int, user_id: int) -> list[ChatMessageDTO]:
        try:
            order = OrderModel.objects.get(pk=order_id)
        except OrderModel.DoesNotExist as exc:
            raise OrderNotFoundError(f"Pedido {order_id} no encontrado") from exc

        _assert_participant(order, user_id)

        messages = (
            OrderChatMessage.objects.filter(order_id=order_id)
            .select_related("sender")
            .order_by("created_at")
        )
        return [_to_dto(m) for m in messages]

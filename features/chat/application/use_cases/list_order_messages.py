from features.chat.application.dto import ListChatMessagesResult
from features.chat.application.participants import assert_chat_participant, is_chat_closed
from features.chat.application.use_cases.send_order_message import message_to_dto
from features.chat.infrastructure.models import OrderChatMessage
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.infrastructure.models import Order as OrderModel


class ListOrderMessagesUseCase:
    def execute(self, order_id: int, user_id: int) -> ListChatMessagesResult:
        try:
            order = OrderModel.objects.select_related("store").get(pk=order_id)
        except OrderModel.DoesNotExist as exc:
            raise OrderNotFoundError(f"Pedido {order_id} no encontrado") from exc

        assert_chat_participant(order, user_id)

        messages = (
            OrderChatMessage.objects.filter(order_id=order_id)
            .select_related("sender")
            .order_by("created_at")
        )
        return ListChatMessagesResult(
            messages=[message_to_dto(m) for m in messages],
            chat_closed=is_chat_closed(order),
        )

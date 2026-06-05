from celery import shared_task

from features.notifications.application.dto import SendPushDTO
from features.notifications.application.use_cases.send_push import SendPushUseCase
from features.notifications.infrastructure.fcm_client import FCMClient, get_fcm_client
from features.notifications.infrastructure.repositories import DjangoDeviceTokenRepository
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.repositories import DjangoOrderRepository


def _build_send_push_use_case(
    fcm_client: FCMClient | None = None,
) -> SendPushUseCase:
    return SendPushUseCase(
        device_token_repository=DjangoDeviceTokenRepository(),
        fcm_client=fcm_client or get_fcm_client(),
    )


@shared_task(
    bind=True,
    max_retries=3,
    name="features.notifications.infrastructure.tasks.notify_customer_task",
)
def notify_customer_task(self, order_id: int) -> str:
    """Stub — notificación al cliente en T2.4.x."""
    return f"pending:{order_id}"


@shared_task(
    bind=True,
    max_retries=3,
    name="features.notifications.infrastructure.tasks.send_push_task",
)
def send_push_task(self, order_id: int, notification_type: str) -> str:
    order_repository = DjangoOrderRepository()
    order = order_repository.get_by_id(order_id)
    if order is None:
        raise OrderNotFoundError(f"Pedido {order_id} no encontrado")

    order_status = OrderStatus(notification_type)
    use_case = _build_send_push_use_case()
    message_ids = use_case.execute(
        SendPushDTO(
            user_id=order.customer_id,
            order_id=order_id,
            order_status=order_status,
        )
    )

    return f"sent:{order_id}:{len(message_ids)}"


@shared_task(
    bind=True,
    max_retries=3,
    name="features.notifications.infrastructure.tasks.notify_drivers_new_order_task",
)
def notify_drivers_new_order_task(self, order_id: int) -> str:
    """Stub — push a conductores online para pedidos listos para recoger."""
    return f"pending-drivers:{order_id}"

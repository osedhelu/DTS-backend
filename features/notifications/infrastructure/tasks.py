from celery import shared_task

from features.delivery.infrastructure.repositories import DjangoDriverAvailabilityRepository
from features.notifications.application.dto import SendPushDTO
from features.notifications.application.recipient_resolver import resolve_recipient_user_ids
from features.notifications.application.use_cases.send_order_email import SendOrderEmailUseCase
from features.notifications.application.use_cases.send_push import SendPushUseCase
from features.notifications.domain.services import OrderStatusNotificationMapper
from features.notifications.infrastructure.fcm_client import FCMClient, get_fcm_client
from features.notifications.infrastructure.repositories import (
    DjangoCustomerEmailRepository,
    DjangoDeviceTokenRepository,
)
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
    return execute_order_push(order_id, OrderStatus.ON_THE_WAY)


def execute_order_push(order_id: int, order_status: str) -> str:
    order_repository = DjangoOrderRepository()
    order = order_repository.get_by_id(order_id)
    if order is None:
        raise OrderNotFoundError(f"Pedido {order_id} no encontrado")

    status = OrderStatus(order_status)
    if not OrderStatusNotificationMapper.supports_status(status):
        return f"skipped:{order_id}:unsupported_status"

    use_case = _build_send_push_use_case()
    user_ids = resolve_recipient_user_ids(
        order,
        status,
        DjangoDriverAvailabilityRepository(),
    )

    message_ids: list[str] = []
    for user_id in user_ids:
        message_ids.extend(
            use_case.execute(
                SendPushDTO(
                    user_id=user_id,
                    order_id=order_id,
                    order_status=status,
                )
            )
        )

    return f"sent:{order_id}:{len(message_ids)}"


@shared_task(
    bind=True,
    max_retries=3,
    name="features.notifications.infrastructure.tasks.send_push_task",
)
def send_push_task(self, order_id: int, notification_type: str) -> str:
    return execute_order_push(order_id, notification_type)


@shared_task(
    bind=True,
    max_retries=3,
    name="features.notifications.infrastructure.tasks.dispatch_order_push_task",
)
def dispatch_order_push_task(self, order_id: int, order_status: str) -> str:
    return execute_order_push(order_id, order_status)


@shared_task(
    bind=True,
    max_retries=3,
    name="features.notifications.infrastructure.tasks.notify_drivers_new_order_task",
)
def notify_drivers_new_order_task(self, order_id: int) -> str:
    """Stub — push a conductores online para pedidos listos para recoger."""
    return f"pending-drivers:{order_id}"


def _build_send_order_email_use_case() -> SendOrderEmailUseCase:
    return SendOrderEmailUseCase(
        order_repository=DjangoOrderRepository(),
        customer_email_repository=DjangoCustomerEmailRepository(),
    )


def execute_order_email(order_id: int, order_status: str) -> str:
    use_case = _build_send_order_email_use_case()
    return use_case.execute(order_id, OrderStatus(order_status))


@shared_task(
    bind=True,
    max_retries=3,
    name="features.notifications.infrastructure.tasks.send_email_notification",
)
def send_email_notification(self, order_id: int, order_status: str) -> str:
    return execute_order_email(order_id, order_status)

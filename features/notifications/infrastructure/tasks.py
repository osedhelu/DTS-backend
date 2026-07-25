import logging

from celery import shared_task

from features.delivery.infrastructure.repositories import DjangoDriverAvailabilityRepository
from features.notifications.application.dto import SendPushDTO
from features.notifications.application.recipient_resolver import resolve_recipient_user_ids
from features.notifications.application.use_cases.send_order_email import SendOrderEmailUseCase
from features.notifications.application.use_cases.send_push import SendPushUseCase
from features.notifications.domain.services import OrderStatusNotificationMapper
from features.notifications.domain.value_objects import NotificationRecipient
from features.notifications.infrastructure.fcm_client import FCMClient, get_fcm_client
from features.notifications.infrastructure.repositories import (
    DjangoCustomerEmailRepository,
    DjangoDeviceTokenRepository,
)
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.repositories import DjangoOrderRepository

logger = logging.getLogger(__name__)


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


def _pickup_location_for_order(store_id: int):
    from features.stores.domain.value_objects import GeoLocation
    from features.stores.infrastructure.models import Store

    try:
        store = Store.objects.only("location").get(pk=store_id)
    except Store.DoesNotExist:
        return None
    return GeoLocation(latitude=store.latitude, longitude=store.longitude)


def _empty_recipients_reason(
    order_status: OrderStatus,
    pickup_location,
) -> str:
    recipients = OrderStatusNotificationMapper.recipients_for_status(order_status)
    if not recipients:
        return "unsupported_recipients"
    if NotificationRecipient.ONLINE_DRIVERS in recipients:
        if pickup_location is None:
            return "no_store_location"
        return "no_online_drivers_in_radius"
    if NotificationRecipient.CUSTOMER in recipients:
        return "no_customer"
    if NotificationRecipient.ASSIGNED_DRIVER in recipients:
        return "no_assigned_driver"
    return "no_recipients"


def execute_order_push(order_id: int, order_status: str) -> str:
    order_repository = DjangoOrderRepository()
    order = order_repository.get_by_id(order_id)
    if order is None:
        raise OrderNotFoundError(f"Pedido {order_id} no encontrado")

    status = OrderStatus(order_status)
    if not OrderStatusNotificationMapper.supports_status(status):
        logger.info(
            "push_skipped order_id=%s status=%s reason=unsupported_status",
            order_id,
            order_status,
        )
        return f"skipped:{order_id}:unsupported_status"

    pickup_location = _pickup_location_for_order(order.store_id)
    user_ids = resolve_recipient_user_ids(
        order,
        status,
        DjangoDriverAvailabilityRepository(),
        pickup_location=pickup_location,
    )

    if not user_ids:
        reason = _empty_recipients_reason(status, pickup_location)
        logger.info(
            "push_skipped order_id=%s status=%s reason=%s "
            "recipient_ids=[] pickup_location=%s",
            order_id,
            status.value,
            reason,
            pickup_location is not None,
        )
        return f"skipped:{order_id}:{reason}"

    logger.info(
        "push_dispatch order_id=%s status=%s recipient_ids=%s",
        order_id,
        status.value,
        user_ids,
    )

    message_ids: list[str] = []
    for user_id in user_ids:
        role = _role_for_user(user_id)
        use_case = _build_send_push_use_case(get_fcm_client(role=role))
        title_override = None
        body_override = None
        if (
            status == OrderStatus.DRIVER_ASSIGNED
            and order.driver_id is not None
            and user_id == order.driver_id
        ):
            title_override = "Pedido asignado"
            body_override = "Aceptaste un pedido. Dirígete al comercio."
        message_ids.extend(
            use_case.execute(
                SendPushDTO(
                    user_id=user_id,
                    order_id=order_id,
                    order_status=status,
                    title_override=title_override,
                    body_override=body_override,
                )
            )
        )

    logger.info(
        "push_finished order_id=%s status=%s recipients=%s message_ids=%s",
        order_id,
        status.value,
        len(user_ids),
        len(message_ids),
    )
    return f"sent:{order_id}:{len(message_ids)}"


def _role_for_user(user_id: int) -> str:
    from features.accounts.domain.entities import UserRole
    from features.accounts.infrastructure.models import CustomUser

    role = (
        CustomUser.objects.filter(pk=user_id)
        .values_list("role", flat=True)
        .first()
    )
    return role or UserRole.CUSTOMER


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
    """Push FCM a conductores online (proyecto dtsdrop) cuando el pedido está listo."""
    return execute_order_push(order_id, OrderStatus.READY_FOR_PICKUP)


def execute_chat_push(order_id: int, recipient_user_id: int, preview: str, sender_role: str = "") -> str:
    from features.notifications.application.dto import SendChatPushDTO

    role = _role_for_user(recipient_user_id)
    use_case = _build_send_push_use_case(get_fcm_client(role=role))
    message_ids = use_case.execute_chat(
        SendChatPushDTO(
            user_id=recipient_user_id,
            order_id=order_id,
            preview=preview,
            sender_role=sender_role,
        )
    )
    return f"chat_sent:{order_id}:{recipient_user_id}:{len(message_ids)}"


@shared_task(
    bind=True,
    max_retries=3,
    name="features.notifications.infrastructure.tasks.notify_chat_message_task",
)
def notify_chat_message_task(
    self,
    order_id: int,
    recipient_user_id: int,
    preview: str,
    sender_role: str = "",
) -> str:
    from features.notifications.domain.exceptions import FCMSendError

    try:
        return execute_chat_push(order_id, recipient_user_id, preview, sender_role)
    except FCMSendError as exc:
        logger.exception(
            "chat_push_failed order_id=%s recipient=%s err=%s",
            order_id,
            recipient_user_id,
            exc,
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries) from exc


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

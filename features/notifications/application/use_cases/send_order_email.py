from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from features.notifications.domain.entities import PushTemplate
from features.notifications.domain.repositories import CustomerEmailRepository
from features.notifications.domain.services import OrderStatusNotificationMapper
from features.notifications.domain.value_objects import NotificationRecipient
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.repositories import OrderRepository
from features.orders.domain.value_objects import OrderStatus

EMAIL_TEMPLATE_TEXT = "notifications/order_status_email.txt"
EMAIL_TEMPLATE_HTML = "notifications/order_status_email.html"


class SendOrderEmailUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        customer_email_repository: CustomerEmailRepository,
    ) -> None:
        self._order_repository = order_repository
        self._customer_email_repository = customer_email_repository

    def execute(self, order_id: int, order_status: OrderStatus) -> str:
        if not OrderStatusNotificationMapper.supports_status(order_status):
            return f"skipped:{order_id}:unsupported_status"

        recipients = OrderStatusNotificationMapper.recipients_for_status(order_status)
        if NotificationRecipient.CUSTOMER not in recipients:
            return f"skipped:{order_id}:no_customer_recipient"

        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Pedido {order_id} no encontrado")

        customer_email = self._customer_email_repository.get_email_for_user(order.customer_id)
        if not customer_email:
            return f"skipped:{order_id}:no_email"

        template = PushTemplate.for_status(order_status)
        context = {
            "order_id": order_id,
            "title": template.title,
            "body": template.body,
            "order_status": order_status.value,
        }

        text_body = render_to_string(EMAIL_TEMPLATE_TEXT, context)
        html_body = render_to_string(EMAIL_TEMPLATE_HTML, context)

        message = EmailMultiAlternatives(
            subject=template.title,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer_email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send()

        return f"sent:{order_id}:{customer_email}"

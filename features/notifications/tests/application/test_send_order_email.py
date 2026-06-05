from unittest.mock import MagicMock

import pytest
from django.template.loader import render_to_string

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.notifications.application.use_cases.send_order_email import (
    EMAIL_TEMPLATE_HTML,
    EMAIL_TEMPLATE_TEXT,
    SendOrderEmailUseCase,
)
from features.notifications.infrastructure.repositories import DjangoCustomerEmailRepository
from features.orders.domain.entities import Order
from features.orders.domain.value_objects import OrderStatus, OrderType


@pytest.mark.django_db
def test_email_template_rendered(mailoutbox):
    customer = CustomUser.objects.create_user(
        username="customer_email",
        email="customer_email@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    order = Order(
        id=42,
        customer_id=customer.id,
        store_id=1,
        status=OrderStatus.ON_THE_WAY,
        order_type=OrderType.DELIVERY,
    )

    context = {
        "order_id": order.id,
        "title": "Pedido en camino",
        "body": "¡Tu pedido ya salió! Va en camino",
        "order_status": OrderStatus.ON_THE_WAY.value,
    }
    text_body = render_to_string(EMAIL_TEMPLATE_TEXT, context)
    html_body = render_to_string(EMAIL_TEMPLATE_HTML, context)

    assert "¡Tu pedido ya salió! Va en camino" in text_body
    assert "Pedido #42" in text_body
    assert "¡Tu pedido ya salió! Va en camino" in html_body
    assert "<strong>" in html_body

    order_repository = MagicMock()
    order_repository.get_by_id.return_value = order
    use_case = SendOrderEmailUseCase(
        order_repository=order_repository,
        customer_email_repository=DjangoCustomerEmailRepository(),
    )

    result = use_case.execute(order.id, OrderStatus.ON_THE_WAY)

    assert result == f"sent:{order.id}:customer_email@test.com"
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == "Pedido en camino"
    assert email.to == ["customer_email@test.com"]
    assert "¡Tu pedido ya salió! Va en camino" in email.body
    assert email.alternatives
    html_content = email.alternatives[0][0]
    assert "¡Tu pedido ya salió! Va en camino" in html_content


@pytest.mark.django_db
def test_send_order_email_skips_driver_only_status(mailoutbox):
    customer = CustomUser.objects.create_user(
        username="customer_email_skip",
        email="skip@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    order = Order(
        id=7,
        customer_id=customer.id,
        store_id=1,
        status=OrderStatus.READY_FOR_PICKUP,
        order_type=OrderType.DELIVERY,
    )

    order_repository = MagicMock()
    order_repository.get_by_id.return_value = order
    use_case = SendOrderEmailUseCase(
        order_repository=order_repository,
        customer_email_repository=DjangoCustomerEmailRepository(),
    )

    result = use_case.execute(order.id, OrderStatus.READY_FOR_PICKUP)

    assert result == "skipped:7:no_customer_recipient"
    assert len(mailoutbox) == 0
    order_repository.get_by_id.assert_not_called()

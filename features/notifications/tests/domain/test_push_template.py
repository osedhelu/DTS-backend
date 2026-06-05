import pytest

from features.notifications.domain.entities import NotificationType, PushTemplate
from features.notifications.domain.exceptions import PushTemplateNotFoundError
from features.orders.domain.value_objects import OrderStatus


def test_notification_types():
    expected = {
        "order_accepted",
        "order_in_preparation",
        "new_order_ready_for_pickup",
        "driver_assigned",
        "order_picked_up",
        "order_on_the_way",
        "order_delivered",
        "order_cancelled",
    }
    assert {member.value for member in NotificationType} == expected
    assert NotificationType.ORDER_ON_THE_WAY == "order_on_the_way"


@pytest.mark.parametrize(
    ("status", "notification_type", "body_fragment"),
    [
        (
            OrderStatus.ACCEPTED_BY_MERCHANT,
            NotificationType.ORDER_ACCEPTED,
            "aceptado",
        ),
        (
            OrderStatus.IN_PREPARATION,
            NotificationType.ORDER_IN_PREPARATION,
            "preparando",
        ),
        (
            OrderStatus.READY_FOR_PICKUP,
            NotificationType.NEW_ORDER_READY_FOR_PICKUP,
            "recoger",
        ),
        (
            OrderStatus.DRIVER_ASSIGNED,
            NotificationType.DRIVER_ASSIGNED,
            "Conductor asignado",
        ),
        (
            OrderStatus.PICKED_UP,
            NotificationType.ORDER_PICKED_UP,
            "recogió",
        ),
        (
            OrderStatus.ON_THE_WAY,
            NotificationType.ORDER_ON_THE_WAY,
            "camino",
        ),
        (
            OrderStatus.DELIVERED,
            NotificationType.ORDER_DELIVERED,
            "entregado",
        ),
        (
            OrderStatus.CANCELLED,
            NotificationType.ORDER_CANCELLED,
            "cancelado",
        ),
    ],
)
def test_push_template_for_status(status, notification_type, body_fragment):
    template = PushTemplate.for_status(status)

    assert template.notification_type == notification_type
    assert template.title
    assert body_fragment.lower() in template.body.lower()


def test_push_template_for_status_raises_when_missing():
    with pytest.raises(PushTemplateNotFoundError, match="created"):
        PushTemplate.for_status(OrderStatus.CREATED)

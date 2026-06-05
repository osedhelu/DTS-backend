import pytest

from features.notifications.domain.services import OrderStatusNotificationMapper
from features.notifications.domain.value_objects import NotificationRecipient
from features.orders.domain.value_objects import OrderStatus


def test_mapper_on_the_way_notifies_customer():
    recipients = OrderStatusNotificationMapper.recipients_for_status(
        OrderStatus.ON_THE_WAY
    )

    assert recipients == frozenset({NotificationRecipient.CUSTOMER})


def test_mapper_ready_for_pickup_notifies_online_drivers():
    recipients = OrderStatusNotificationMapper.recipients_for_status(
        OrderStatus.READY_FOR_PICKUP
    )

    assert recipients == frozenset({NotificationRecipient.ONLINE_DRIVERS})


@pytest.mark.parametrize(
    "status",
    [
        OrderStatus.CREATED,
        OrderStatus.SEARCHING_DRIVER,
        OrderStatus.SCHEDULED,
    ],
)
def test_mapper_returns_empty_for_unsupported_statuses(status):
    recipients = OrderStatusNotificationMapper.recipients_for_status(status)

    assert recipients == frozenset()
    assert not OrderStatusNotificationMapper.supports_status(status)

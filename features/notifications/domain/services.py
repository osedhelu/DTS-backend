from features.notifications.domain.value_objects import NotificationRecipient
from features.orders.domain.value_objects import OrderStatus

_CUSTOMER_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.ACCEPTED_BY_MERCHANT,
        OrderStatus.IN_PREPARATION,
        OrderStatus.DRIVER_ASSIGNED,
        OrderStatus.PICKED_UP,
        OrderStatus.ON_THE_WAY,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    }
)


class OrderStatusNotificationMapper:
    """Mapea un estado de pedido a los destinatarios de push."""

    @staticmethod
    def recipients_for_status(status: OrderStatus) -> frozenset[NotificationRecipient]:
        if status == OrderStatus.READY_FOR_PICKUP:
            return frozenset({NotificationRecipient.ONLINE_DRIVERS})

        if status in _CUSTOMER_STATUSES:
            return frozenset({NotificationRecipient.CUSTOMER})

        return frozenset()

    @staticmethod
    def supports_status(status: OrderStatus) -> bool:
        return bool(OrderStatusNotificationMapper.recipients_for_status(status))

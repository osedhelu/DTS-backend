from features.orders.domain.value_objects import OrderStatus

TRACKABLE_ORDER_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.DRIVER_ASSIGNED,
        OrderStatus.PICKED_UP,
        OrderStatus.ON_THE_WAY,
    }
)

from features.orders.domain.value_objects import OrderStatus

TRACKABLE_ORDER_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.DRIVER_ASSIGNED,
        OrderStatus.PICKED_UP,
        OrderStatus.ON_THE_WAY,
    }
)

ASSIGNABLE_ORDER_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.READY_FOR_PICKUP,
        OrderStatus.SEARCHING_DRIVER,
    }
)

from features.orders.domain.exceptions import InvalidOrderTransitionError
from features.orders.domain.value_objects import DELIVERY_STATUSES, OrderStatus

CANCELLABLE_BEFORE_PICKUP: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.CREATED,
        OrderStatus.ACCEPTED_BY_MERCHANT,
        OrderStatus.IN_PREPARATION,
        OrderStatus.READY_FOR_PICKUP,
        OrderStatus.SEARCHING_DRIVER,
        OrderStatus.DRIVER_ASSIGNED,
    }
)

DELIVERY_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.CREATED: frozenset(
        {OrderStatus.ACCEPTED_BY_MERCHANT, OrderStatus.CANCELLED}
    ),
    OrderStatus.ACCEPTED_BY_MERCHANT: frozenset(
        {OrderStatus.IN_PREPARATION, OrderStatus.CANCELLED}
    ),
    OrderStatus.IN_PREPARATION: frozenset(
        {OrderStatus.READY_FOR_PICKUP, OrderStatus.CANCELLED}
    ),
    OrderStatus.READY_FOR_PICKUP: frozenset(
        {OrderStatus.SEARCHING_DRIVER, OrderStatus.CANCELLED}
    ),
    OrderStatus.SEARCHING_DRIVER: frozenset(
        {OrderStatus.DRIVER_ASSIGNED, OrderStatus.CANCELLED}
    ),
    OrderStatus.DRIVER_ASSIGNED: frozenset(
        {OrderStatus.PICKED_UP, OrderStatus.CANCELLED}
    ),
    OrderStatus.PICKED_UP: frozenset({OrderStatus.ON_THE_WAY}),
    OrderStatus.ON_THE_WAY: frozenset({OrderStatus.DELIVERED}),
    OrderStatus.DELIVERED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


class OrderStateMachine:
    """Máquina de estados para pedidos de delivery (productos físicos)."""

    @staticmethod
    def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
        if current not in DELIVERY_STATUSES or target not in DELIVERY_STATUSES:
            return False
        return target in DELIVERY_TRANSITIONS.get(current, frozenset())

    @staticmethod
    def transition(current: OrderStatus, target: OrderStatus) -> OrderStatus:
        if not OrderStateMachine.can_transition(current, target):
            raise InvalidOrderTransitionError(
                f"Transición inválida de '{current}' a '{target}'"
            )
        return target

    @staticmethod
    def allowed_transitions(current: OrderStatus) -> frozenset[OrderStatus]:
        if current not in DELIVERY_STATUSES:
            return frozenset()
        return DELIVERY_TRANSITIONS.get(current, frozenset())

    @staticmethod
    def can_cancel(current: OrderStatus) -> bool:
        return current in CANCELLABLE_BEFORE_PICKUP

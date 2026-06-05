from enum import StrEnum


class OrderStatus(StrEnum):
    """Estados de un pedido en la plataforma (delivery y servicios a domicilio)."""

    # Compartidos
    CREATED = "created"
    ACCEPTED_BY_MERCHANT = "accepted_by_merchant"
    CANCELLED = "cancelled"

    # Delivery — productos físicos con conductor
    IN_PREPARATION = "in_preparation"
    READY_FOR_PICKUP = "ready_for_pickup"
    SEARCHING_DRIVER = "searching_driver"
    DRIVER_ASSIGNED = "driver_assigned"
    PICKED_UP = "picked_up"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"

    # Servicio — visita a domicilio sin conductor de plataforma
    SCHEDULED = "scheduled"
    PROVIDER_EN_ROUTE = "provider_en_route"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


DELIVERY_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.CREATED,
        OrderStatus.ACCEPTED_BY_MERCHANT,
        OrderStatus.IN_PREPARATION,
        OrderStatus.READY_FOR_PICKUP,
        OrderStatus.SEARCHING_DRIVER,
        OrderStatus.DRIVER_ASSIGNED,
        OrderStatus.PICKED_UP,
        OrderStatus.ON_THE_WAY,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    }
)

SERVICE_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.CREATED,
        OrderStatus.ACCEPTED_BY_MERCHANT,
        OrderStatus.SCHEDULED,
        OrderStatus.PROVIDER_EN_ROUTE,
        OrderStatus.IN_PROGRESS,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    }
)

TERMINAL_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.DELIVERED,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    }
)

"""OrderStatus — implementar state machine en T1.5.1 y T1.5.2."""
from enum import StrEnum


class OrderStatus(StrEnum):
    CREATED = "created"
    ACCEPTED_BY_MERCHANT = "accepted_by_merchant"
    IN_PREPARATION = "in_preparation"
    READY_FOR_PICKUP = "ready_for_pickup"
    SEARCHING_DRIVER = "searching_driver"
    DRIVER_ASSIGNED = "driver_assigned"
    PICKED_UP = "picked_up"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

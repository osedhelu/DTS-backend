from features.orders.domain.value_objects import (
    DELIVERY_STATUSES,
    SERVICE_STATUSES,
    TERMINAL_STATUSES,
    OrderStatus,
)


def test_all_status_values_defined():
    expected = {
        "created": OrderStatus.CREATED,
        "accepted_by_merchant": OrderStatus.ACCEPTED_BY_MERCHANT,
        "cancelled": OrderStatus.CANCELLED,
        "in_preparation": OrderStatus.IN_PREPARATION,
        "ready_for_pickup": OrderStatus.READY_FOR_PICKUP,
        "searching_driver": OrderStatus.SEARCHING_DRIVER,
        "driver_assigned": OrderStatus.DRIVER_ASSIGNED,
        "picked_up": OrderStatus.PICKED_UP,
        "on_the_way": OrderStatus.ON_THE_WAY,
        "delivered": OrderStatus.DELIVERED,
        "scheduled": OrderStatus.SCHEDULED,
        "provider_en_route": OrderStatus.PROVIDER_EN_ROUTE,
        "in_progress": OrderStatus.IN_PROGRESS,
        "completed": OrderStatus.COMPLETED,
    }

    assert len(OrderStatus) == len(expected)
    for value, status in expected.items():
        assert status == value
        assert OrderStatus(value) is status

    assert DELIVERY_STATUSES | SERVICE_STATUSES == set(OrderStatus)
    assert OrderStatus.DELIVERED in TERMINAL_STATUSES
    assert OrderStatus.COMPLETED in TERMINAL_STATUSES
    assert OrderStatus.CANCELLED in TERMINAL_STATUSES

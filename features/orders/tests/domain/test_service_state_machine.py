import pytest

from features.orders.domain.exceptions import InvalidOrderTransitionError
from features.orders.domain.services import (
    DRIVER_RELATED_STATUSES,
    ServiceOrderStateMachine,
)
from features.orders.domain.value_objects import OrderStatus


def test_service_order_valid_transitions():
    flow = [
        OrderStatus.CREATED,
        OrderStatus.ACCEPTED_BY_MERCHANT,
        OrderStatus.SCHEDULED,
        OrderStatus.PROVIDER_EN_ROUTE,
        OrderStatus.IN_PROGRESS,
        OrderStatus.COMPLETED,
    ]

    for current, target in zip(flow, flow[1:], strict=False):
        assert ServiceOrderStateMachine.can_transition(current, target)
        assert ServiceOrderStateMachine.transition(current, target) == target

    assert ServiceOrderStateMachine.can_cancel(OrderStatus.SCHEDULED) is True
    assert ServiceOrderStateMachine.can_cancel(OrderStatus.IN_PROGRESS) is False

    assert ServiceOrderStateMachine.transition(
        OrderStatus.CREATED, OrderStatus.CANCELLED
    ) == OrderStatus.CANCELLED


def test_service_order_skips_driver_states():
    for driver_status in DRIVER_RELATED_STATUSES:
        assert ServiceOrderStateMachine.can_transition(
            OrderStatus.ACCEPTED_BY_MERCHANT,
            driver_status,
        ) is False

        with pytest.raises(InvalidOrderTransitionError):
            ServiceOrderStateMachine.transition(
                OrderStatus.ACCEPTED_BY_MERCHANT,
                driver_status,
            )

    assert ServiceOrderStateMachine.can_transition(
        OrderStatus.ACCEPTED_BY_MERCHANT,
        OrderStatus.SCHEDULED,
    )

    with pytest.raises(InvalidOrderTransitionError):
        ServiceOrderStateMachine.transition(
            OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED
        )

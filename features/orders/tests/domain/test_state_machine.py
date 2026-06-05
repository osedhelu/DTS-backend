import pytest

from features.orders.domain.exceptions import InvalidOrderTransitionError
from features.orders.domain.services import OrderStateMachine
from features.orders.domain.value_objects import OrderStatus


def test_valid_transition_created_to_accepted():
    assert OrderStateMachine.can_transition(
        OrderStatus.CREATED,
        OrderStatus.ACCEPTED_BY_MERCHANT,
    )

    result = OrderStateMachine.transition(
        OrderStatus.CREATED,
        OrderStatus.ACCEPTED_BY_MERCHANT,
    )

    assert result == OrderStatus.ACCEPTED_BY_MERCHANT


def test_invalid_transition_raises():
    with pytest.raises(InvalidOrderTransitionError, match="Transición inválida"):
        OrderStateMachine.transition(OrderStatus.CREATED, OrderStatus.DELIVERED)

    with pytest.raises(InvalidOrderTransitionError):
        OrderStateMachine.transition(OrderStatus.CREATED, OrderStatus.SCHEDULED)

    with pytest.raises(InvalidOrderTransitionError):
        OrderStateMachine.transition(OrderStatus.PICKED_UP, OrderStatus.CANCELLED)

    assert OrderStateMachine.can_cancel(OrderStatus.PICKED_UP) is False
    assert OrderStateMachine.can_cancel(OrderStatus.CREATED) is True

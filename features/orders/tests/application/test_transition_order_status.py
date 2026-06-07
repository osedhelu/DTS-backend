from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from features.accounts.domain.entities import UserRole
from features.orders.application.dto import TransitionOrderStatusDTO
from features.orders.application.use_cases.transition_order_status import (
    TransitionOrderStatusUseCase,
)
from features.orders.domain.entities import Order
from features.orders.domain.exceptions import UnauthorizedOrderTransitionError
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.stores.domain.entities import Store, StoreStatus


def test_merchant_accepts_order():
    order_repository = MagicMock()
    store_repository = MagicMock()

    order = Order(
        id=1,
        customer_id=5,
        store_id=10,
        status=OrderStatus.CREATED,
    )
    order_repository.get_by_id.return_value = order
    store_repository.get_by_id.return_value = Store(
        id=10, name="Restaurante", owner_id=20, status=StoreStatus.OPEN
    )
    accepted = Order(
        id=1,
        customer_id=5,
        store_id=10,
        status=OrderStatus.ACCEPTED_BY_MERCHANT,
    )
    order_repository.update_status.return_value = accepted

    use_case = TransitionOrderStatusUseCase(order_repository, store_repository)
    result = use_case.execute(
        TransitionOrderStatusDTO(
            order_id=1,
            target_status=OrderStatus.ACCEPTED_BY_MERCHANT,
            actor_id=20,
            actor_role=UserRole.MERCHANT,
        )
    )

    order_repository.update_status.assert_called_once_with(
        1, OrderStatus.ACCEPTED_BY_MERCHANT
    )
    assert result.status == OrderStatus.ACCEPTED_BY_MERCHANT


def test_customer_cannot_accept():
    order_repository = MagicMock()
    store_repository = MagicMock()

    order_repository.get_by_id.return_value = Order(
        id=1,
        customer_id=5,
        store_id=10,
        status=OrderStatus.CREATED,
    )

    use_case = TransitionOrderStatusUseCase(order_repository, store_repository)

    with pytest.raises(UnauthorizedOrderTransitionError, match="cliente no puede"):
        use_case.execute(
            TransitionOrderStatusDTO(
                order_id=1,
                target_status=OrderStatus.ACCEPTED_BY_MERCHANT,
                actor_id=5,
                actor_role=UserRole.CUSTOMER,
            )
        )

    order_repository.update_status.assert_not_called()
    store_repository.get_by_id.assert_not_called()


def test_merchant_schedules_service_order():
    order_repository = MagicMock()
    store_repository = MagicMock()

    order = Order(
        id=2,
        customer_id=5,
        store_id=10,
        status=OrderStatus.ACCEPTED_BY_MERCHANT,
        order_type=OrderType.SERVICE,
    )
    order_repository.get_by_id.return_value = order
    store_repository.get_by_id.return_value = Store(
        id=10, name="Limpieza Express", owner_id=20, status=StoreStatus.OPEN
    )
    scheduled = Order(
        id=2,
        customer_id=5,
        store_id=10,
        status=OrderStatus.SCHEDULED,
        order_type=OrderType.SERVICE,
    )
    order_repository.update_status.return_value = scheduled

    use_case = TransitionOrderStatusUseCase(order_repository, store_repository)
    result = use_case.execute(
        TransitionOrderStatusDTO(
            order_id=2,
            target_status=OrderStatus.SCHEDULED,
            actor_id=20,
            actor_role=UserRole.MERCHANT,
        )
    )

    order_repository.update_status.assert_called_once_with(2, OrderStatus.SCHEDULED)
    assert result.status == OrderStatus.SCHEDULED

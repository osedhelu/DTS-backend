from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from features.orders.application.dto import CreateOrderDTO, OrderLineDTO
from features.orders.application.use_cases.create_order import CreateOrderUseCase
from features.orders.domain.entities import Order, OrderItem
from features.orders.domain.exceptions import EmptyCartError
from features.orders.domain.value_objects import OrderStatus
from features.products.domain.entities import Product, ProductType
from features.products.domain.exceptions import InsufficientStockError
from features.stores.domain.entities import Store, StoreStatus


def test_create_order_with_items():
    order_repository = MagicMock()
    product_repository = MagicMock()
    store_repository = MagicMock()

    store_repository.get_by_id.return_value = Store(
        id=1, name="Restaurante", owner_id=10, status=StoreStatus.OPEN
    )
    product_repository.get_by_id.side_effect = lambda pid: {
        1: Product(
            id=1,
            name="Hamburguesa",
            price=Decimal("15990"),
            store_id=1,
            stock=10,
            product_type=ProductType.PHYSICAL,
        ),
        2: Product(
            id=2,
            name="Limpieza profunda",
            price=Decimal("85000"),
            store_id=1,
            product_type=ProductType.SERVICE,
        ),
    }[pid]

    created = Order(
        id=100,
        customer_id=5,
        store_id=1,
        status=OrderStatus.CREATED,
        items=[
            OrderItem(
                product_id=1,
                product_name="Hamburguesa",
                unit_price=Decimal("15990"),
                quantity=2,
            ),
            OrderItem(
                product_id=2,
                product_name="Limpieza profunda",
                unit_price=Decimal("85000"),
                quantity=1,
            ),
        ],
    )
    order_repository.create.return_value = created

    use_case = CreateOrderUseCase(order_repository, product_repository, store_repository)
    result = use_case.execute(
        CreateOrderDTO(
            customer_id=5,
            store_id=1,
            items=(
                OrderLineDTO(product_id=1, quantity=2),
                OrderLineDTO(product_id=2, quantity=1),
            ),
        )
    )

    order_repository.create.assert_called_once()
    payload = order_repository.create.call_args[0][0]
    assert payload["customer_id"] == 5
    assert payload["store_id"] == 1
    assert payload["status"] == OrderStatus.CREATED
    assert len(payload["items"]) == 2
    assert payload["items"][0]["product_name"] == "Hamburguesa"
    assert result.total == Decimal("116980")
    assert result.status == OrderStatus.CREATED


def test_empty_cart_fails():
    order_repository = MagicMock()
    product_repository = MagicMock()
    store_repository = MagicMock()

    use_case = CreateOrderUseCase(order_repository, product_repository, store_repository)

    with pytest.raises(EmptyCartError, match="sin ítems"):
        use_case.execute(CreateOrderDTO(customer_id=5, store_id=1, items=()))

    order_repository.create.assert_not_called()
    product_repository.get_by_id.assert_not_called()


def test_create_order_insufficient_stock():
    order_repository = MagicMock()
    product_repository = MagicMock()
    store_repository = MagicMock()

    store_repository.get_by_id.return_value = Store(
        id=1, name="Restaurante", owner_id=10, status=StoreStatus.OPEN
    )
    product_repository.get_by_id.return_value = Product(
        id=1,
        name="Hamburguesa",
        price=Decimal("15990"),
        store_id=1,
        stock=1,
        product_type=ProductType.PHYSICAL,
    )

    use_case = CreateOrderUseCase(order_repository, product_repository, store_repository)

    with pytest.raises(InsufficientStockError):
        use_case.execute(
            CreateOrderDTO(
                customer_id=5,
                store_id=1,
                items=(OrderLineDTO(product_id=1, quantity=5),),
            )
        )

    order_repository.create.assert_not_called()

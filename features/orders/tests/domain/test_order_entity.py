from decimal import Decimal

import pytest

from features.orders.domain.entities import Order, OrderItem
from features.orders.domain.exceptions import InvalidOrderItemError
from features.orders.domain.value_objects import OrderStatus


def test_order_total_calculation():
    items = [
        OrderItem(
            product_id=1,
            product_name="Hamburguesa clásica",
            unit_price=Decimal("15990.00"),
            quantity=2,
        ),
        OrderItem(
            product_id=2,
            product_name="Papas medianas",
            unit_price=Decimal("5900.00"),
            quantity=1,
        ),
        OrderItem(
            product_id=3,
            product_name="Limpieza profunda",
            unit_price=Decimal("85000.00"),
            quantity=1,
        ),
    ]

    order = Order(
        id=1,
        customer_id=10,
        store_id=5,
        items=items,
        status=OrderStatus.CREATED,
    )

    assert order.total == Decimal("122880.00")
    assert order.item_count == 4
    assert items[0].subtotal == Decimal("31980.00")

    with pytest.raises(InvalidOrderItemError):
        OrderItem(
            product_id=4,
            product_name="Inválido",
            unit_price=Decimal("0"),
            quantity=1,
        )

    with pytest.raises(InvalidOrderItemError):
        OrderItem(
            product_id=5,
            product_name="Inválido",
            unit_price=Decimal("1000"),
            quantity=0,
        )

from unittest.mock import MagicMock

from features.delivery.domain.services import OnlineDriver
from features.notifications.application.recipient_resolver import resolve_recipient_user_ids
from features.orders.domain.entities import Order
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.stores.domain.value_objects import GeoLocation


def test_resolve_recipient_user_ids_for_on_the_way_customer():
    order = Order(
        id=42,
        customer_id=10,
        store_id=5,
        status=OrderStatus.ON_THE_WAY,
        order_type=OrderType.DELIVERY,
    )
    driver_repository = MagicMock()

    user_ids = resolve_recipient_user_ids(
        order,
        OrderStatus.ON_THE_WAY,
        driver_repository,
    )

    assert user_ids == [10]
    driver_repository.list_online_drivers.assert_not_called()


def test_resolve_recipient_user_ids_for_ready_for_pickup_drivers():
    order = Order(
        id=42,
        customer_id=10,
        store_id=5,
        status=OrderStatus.READY_FOR_PICKUP,
        order_type=OrderType.DELIVERY,
    )
    driver_repository = MagicMock()
    driver_repository.list_online_drivers.return_value = [
        OnlineDriver(driver_id=21, location=GeoLocation(latitude=4.71, longitude=-74.07)),
        OnlineDriver(driver_id=22, location=GeoLocation(latitude=4.72, longitude=-74.08)),
    ]

    user_ids = resolve_recipient_user_ids(
        order,
        OrderStatus.READY_FOR_PICKUP,
        driver_repository,
    )

    assert user_ids == [21, 22]

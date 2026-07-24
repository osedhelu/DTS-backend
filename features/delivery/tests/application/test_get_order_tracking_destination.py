from unittest.mock import MagicMock

from features.delivery.application.use_cases.get_order_tracking import (
    GetOrderTrackingUseCase,
)
from features.orders.domain.value_objects import OrderStatus


def _order(*, status, customer_id=1, store_id=2, lat=None, lng=None):
    order = MagicMock()
    order.id = 10
    order.customer_id = customer_id
    order.store_id = store_id
    order.status = status
    if lat is None:
        order.service_details = None
    else:
        details = MagicMock()
        details.latitude = lat
        details.longitude = lng
        order.service_details = details
    return order


def test_tracking_destination_uses_delivery_coords_on_the_way():
    order_repo = MagicMock()
    tracking_repo = MagicMock()
    store_repo = MagicMock()
    order_repo.get_by_id.return_value = _order(
        status=OrderStatus.ON_THE_WAY, lat=4.7, lng=-74.0
    )
    tracking_repo.get_by_order_id.return_value = None
    store = MagicMock()
    store.latitude = 4.1
    store.longitude = -74.1
    store_repo.get_by_id.return_value = store

    result = GetOrderTrackingUseCase(order_repo, tracking_repo, store_repo).execute(
        10, 1
    )
    assert result.destination_latitude == 4.7
    assert result.destination_longitude == -74.0


def test_tracking_on_the_way_without_delivery_coords_does_not_fallback_store():
    order_repo = MagicMock()
    tracking_repo = MagicMock()
    store_repo = MagicMock()
    order_repo.get_by_id.return_value = _order(status=OrderStatus.ON_THE_WAY)
    tracking_repo.get_by_order_id.return_value = None
    store = MagicMock()
    store.latitude = 4.1
    store.longitude = -74.1
    store_repo.get_by_id.return_value = store

    result = GetOrderTrackingUseCase(order_repo, tracking_repo, store_repo).execute(
        10, 1
    )
    assert result.destination_latitude is None
    assert result.destination_longitude is None

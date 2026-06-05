from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from features.delivery.application.dto import RecordLocationDTO
from features.delivery.application.use_cases.record_location import RecordLocationUseCase
from features.delivery.domain.entities import DeliveryTracking
from features.delivery.domain.exceptions import (
    InvalidOrderStatusForTrackingError,
    ServiceOrderNotTrackableError,
    UnauthorizedDriverError,
)
from features.orders.domain.entities import Order
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.value_objects import OrderStatus, OrderType


def test_record_driver_location():
    order_repository = MagicMock()
    tracking_repository = MagicMock()

    order = Order(
        id=1,
        customer_id=5,
        store_id=10,
        driver_id=7,
        status=OrderStatus.ON_THE_WAY,
    )
    order_repository.get_by_id.return_value = order
    tracking_repository.get_or_create.return_value = DeliveryTracking(order_id=1, id=1)
    tracking_repository.save.side_effect = lambda tracking: tracking

    use_case = RecordLocationUseCase(order_repository, tracking_repository)
    recorded_at = datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc)

    result = use_case.execute(
        RecordLocationDTO(
            order_id=1,
            driver_id=7,
            latitude=4.7110,
            longitude=-74.0721,
            recorded_at=recorded_at,
        )
    )

    order_repository.get_by_id.assert_called_once_with(1)
    tracking_repository.get_or_create.assert_called_once_with(1)
    tracking_repository.save.assert_called_once()
    assert result.point_count == 1
    assert result.latest_point is not None
    assert result.latest_point.latitude == 4.7110
    assert result.latest_point.longitude == -74.0721
    assert result.latest_point.sequence == 1
    assert result.latest_point.recorded_at == recorded_at


def test_record_driver_location_rejects_unassigned_driver():
    order_repository = MagicMock()
    tracking_repository = MagicMock()

    order_repository.get_by_id.return_value = Order(
        id=1,
        customer_id=5,
        store_id=10,
        driver_id=7,
        status=OrderStatus.ON_THE_WAY,
    )

    use_case = RecordLocationUseCase(order_repository, tracking_repository)

    with pytest.raises(UnauthorizedDriverError, match="no está asignado"):
        use_case.execute(
            RecordLocationDTO(
                order_id=1,
                driver_id=99,
                latitude=4.7110,
                longitude=-74.0721,
                recorded_at=datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
            )
        )

    tracking_repository.get_or_create.assert_not_called()
    tracking_repository.save.assert_not_called()


def test_record_driver_location_rejects_invalid_status():
    order_repository = MagicMock()
    tracking_repository = MagicMock()

    order_repository.get_by_id.return_value = Order(
        id=1,
        customer_id=5,
        store_id=10,
        driver_id=7,
        status=OrderStatus.DELIVERED,
    )

    use_case = RecordLocationUseCase(order_repository, tracking_repository)

    with pytest.raises(InvalidOrderStatusForTrackingError, match="no admite registro"):
        use_case.execute(
            RecordLocationDTO(
                order_id=1,
                driver_id=7,
                latitude=4.7110,
                longitude=-74.0721,
                recorded_at=datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
            )
        )

    tracking_repository.get_or_create.assert_not_called()


def test_record_driver_location_rejects_service_order():
    order_repository = MagicMock()
    tracking_repository = MagicMock()

    order_repository.get_by_id.return_value = Order(
        id=1,
        customer_id=5,
        store_id=10,
        driver_id=7,
        status=OrderStatus.ON_THE_WAY,
        order_type=OrderType.SERVICE,
    )

    use_case = RecordLocationUseCase(order_repository, tracking_repository)

    with pytest.raises(ServiceOrderNotTrackableError, match="delivery admiten tracking"):
        use_case.execute(
            RecordLocationDTO(
                order_id=1,
                driver_id=7,
                latitude=4.7110,
                longitude=-74.0721,
                recorded_at=datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
            )
        )

    tracking_repository.get_or_create.assert_not_called()


def test_record_driver_location_order_not_found():
    order_repository = MagicMock()
    tracking_repository = MagicMock()
    order_repository.get_by_id.return_value = None

    use_case = RecordLocationUseCase(order_repository, tracking_repository)

    with pytest.raises(OrderNotFoundError, match="no encontrado"):
        use_case.execute(
            RecordLocationDTO(
                order_id=404,
                driver_id=7,
                latitude=4.7110,
                longitude=-74.0721,
                recorded_at=datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
            )
        )

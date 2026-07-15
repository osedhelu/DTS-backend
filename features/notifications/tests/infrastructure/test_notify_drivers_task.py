from unittest.mock import patch

import pytest

from features.orders.domain.value_objects import OrderStatus


def _geos_available() -> bool:
    try:
        from django.contrib.gis.geos import Point

        Point(0, 0, srid=4326)
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido para importar tasks con PostGIS",
)
def test_notify_drivers_new_order_task_delegates_to_ready_for_pickup():
    with patch(
        "features.notifications.infrastructure.tasks.execute_order_push",
        return_value="sent:99:2",
    ) as mock_execute:
        from features.notifications.infrastructure.tasks import (
            notify_drivers_new_order_task,
        )

        result = notify_drivers_new_order_task.run(99)

    assert result == "sent:99:2"
    mock_execute.assert_called_once_with(99, OrderStatus.READY_FOR_PICKUP)

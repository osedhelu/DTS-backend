from datetime import datetime, timezone

import pytest

from features.delivery.domain.entities import DeliveryTracking
from features.delivery.domain.exceptions import InvalidTrackingPointError
from features.stores.domain.exceptions import InvalidGeoLocationError


def test_tracking_point_sequence():
    tracking = DeliveryTracking(order_id=42)

    first = tracking.add_point(
        latitude=4.7110,
        longitude=-74.0721,
        recorded_at=datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )
    second = tracking.add_point(
        latitude=4.7120,
        longitude=-74.0710,
        recorded_at=datetime(2026, 6, 4, 14, 0, 10, tzinfo=timezone.utc),
    )
    third = tracking.add_point(
        latitude=4.7130,
        longitude=-74.0700,
        recorded_at=datetime(2026, 6, 4, 14, 0, 20, tzinfo=timezone.utc),
    )

    assert tracking.point_count == 3
    assert [point.sequence for point in tracking.points] == [1, 2, 3]
    assert first.sequence == 1
    assert second.sequence == 2
    assert third.sequence == 3
    assert tracking.latest_point == third

    with pytest.raises(InvalidTrackingPointError, match="orden cronológico"):
        tracking.add_point(
            latitude=4.7140,
            longitude=-74.0690,
            recorded_at=datetime(2026, 6, 4, 14, 0, 5, tzinfo=timezone.utc),
        )

    with pytest.raises(InvalidGeoLocationError):
        tracking.add_point(
            latitude=999.0,
            longitude=-74.0690,
            recorded_at=datetime(2026, 6, 4, 14, 0, 30, tzinfo=timezone.utc),
        )

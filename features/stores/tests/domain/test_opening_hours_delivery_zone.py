import pytest
from datetime import time

from features.stores.domain.services import (
    DeliveryZoneService,
    OpeningHoursService,
    OpeningHoursSlot,
    haversine_km,
)
from features.stores.domain.value_objects import GeoLocation


def test_haversine_km_same_point():
    assert haversine_km(4.71, -74.07, 4.71, -74.07) == pytest.approx(0.0, abs=0.01)


def test_opening_hours_open_now():
    slots = [
        OpeningHoursSlot(
            day_of_week=0,
            open_time=time(8, 0),
            close_time=time(22, 0),
            is_closed=False,
        )
    ]
    from datetime import datetime

    monday_noon = datetime(2026, 7, 13, 12, 0)
    assert OpeningHoursService.is_open_now(slots, now=monday_noon) is True


def test_delivery_zone_within_radius():
    zones = [(4.71, -74.07, 5, True)]
    customer = GeoLocation(latitude=4.715, longitude=-74.075)
    assert DeliveryZoneService.is_within_any_zone(zones, customer) is True


def test_delivery_zone_outside_radius():
    zones = [(4.71, -74.07, 1, True)]
    customer = GeoLocation(latitude=4.80, longitude=-74.07)
    assert DeliveryZoneService.is_within_any_zone(zones, customer) is False

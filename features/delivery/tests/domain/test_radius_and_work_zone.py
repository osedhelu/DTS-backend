import pytest

from features.delivery.domain.constants import (
    DEFAULT_RADIUS_KM,
    MAX_RADIUS_KM,
    MIN_RADIUS_KM,
    normalize_radius_km,
)
from features.delivery.domain.services import DriverMatcher, OnlineDriver
from features.stores.domain.value_objects import GeoLocation

_STORE = GeoLocation(latitude=4.7100, longitude=-74.0720)


def test_normalize_radius_km_defaults_and_bounds():
    assert normalize_radius_km(None) == DEFAULT_RADIUS_KM
    assert normalize_radius_km(35) == 35.0
    assert normalize_radius_km("10") == 10.0
    with pytest.raises(ValueError):
        normalize_radius_km(0.5)
    with pytest.raises(ValueError):
        normalize_radius_km(MAX_RADIUS_KM + 1)
    with pytest.raises(ValueError):
        normalize_radius_km("abc")
    assert MIN_RADIUS_KM == 1.0
    assert MAX_RADIUS_KM == 500.0


def test_driver_covers_store_uses_work_center_and_radius():
    # GPS lejos, zona cerca con radio 35 km
    driver = OnlineDriver(
        driver_id=1,
        location=GeoLocation(latitude=5.0, longitude=-74.0),
        work_center=_STORE,
        work_radius_km=35.0,
    )
    near_store = GeoLocation(latitude=4.7300, longitude=-74.0720)  # ~2 km
    far_store = GeoLocation(latitude=5.2000, longitude=-74.0720)  # ~50+ km

    assert DriverMatcher.driver_covers_store(driver, near_store) is True
    assert DriverMatcher.driver_covers_store(driver, far_store) is False


def test_driver_covers_store_fallback_gps_default_radius():
    near = OnlineDriver(
        driver_id=2,
        location=GeoLocation(latitude=4.7300, longitude=-74.0720),
    )
    far = OnlineDriver(
        driver_id=3,
        location=GeoLocation(latitude=4.8100, longitude=-74.0720),
    )
    assert DriverMatcher.driver_covers_store(near, _STORE) is True
    assert DriverMatcher.driver_covers_store(far, _STORE) is False

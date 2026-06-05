import pytest

from features.delivery.domain.exceptions import NoDriverAvailableError
from features.delivery.domain.services import DriverMatcher, OnlineDriver
from features.stores.domain.value_objects import GeoLocation


def test_find_nearest_driver():
    pickup = GeoLocation(latitude=4.7110, longitude=-74.0721)
    drivers = [
        OnlineDriver(driver_id=1, location=GeoLocation(latitude=4.6500, longitude=-74.1000)),
        OnlineDriver(driver_id=2, location=GeoLocation(latitude=4.7120, longitude=-74.0710)),
        OnlineDriver(driver_id=3, location=GeoLocation(latitude=4.8000, longitude=-74.0000)),
    ]

    nearest = DriverMatcher.find_nearest_driver(pickup, drivers)

    assert nearest.driver_id == 2


def test_no_driver_available():
    pickup = GeoLocation(latitude=4.7110, longitude=-74.0721)

    with pytest.raises(NoDriverAvailableError, match="conductores online"):
        DriverMatcher.find_nearest_driver(pickup, [])

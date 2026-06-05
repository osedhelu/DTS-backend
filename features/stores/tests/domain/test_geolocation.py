import pytest

from features.stores.domain.exceptions import InvalidGeoLocationError
from features.stores.domain.value_objects import GeoLocation


def test_geolocation_validation():
    location = GeoLocation(latitude=4.7110, longitude=-74.0721)
    assert location.latitude == 4.7110
    assert location.longitude == -74.0721
    assert str(location) == "4.711,-74.0721"


@pytest.mark.parametrize(
    "latitude,longitude",
    [
        (91.0, 0.0),
        (-91.0, 0.0),
        (0.0, 181.0),
        (0.0, -181.0),
    ],
)
def test_geolocation_invalid_coordinates_raise(latitude, longitude):
    with pytest.raises(InvalidGeoLocationError):
        GeoLocation(latitude=latitude, longitude=longitude)

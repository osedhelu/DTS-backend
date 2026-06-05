from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

from features.delivery.domain.exceptions import NoDriverAvailableError
from features.stores.domain.value_objects import GeoLocation

EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True, slots=True)
class OnlineDriver:
    driver_id: int
    location: GeoLocation


class DriverMatcher:
    @staticmethod
    def find_nearest_driver(
        pickup_location: GeoLocation,
        online_drivers: list[OnlineDriver],
    ) -> OnlineDriver:
        if not online_drivers:
            raise NoDriverAvailableError("No hay conductores online disponibles")

        return min(
            online_drivers,
            key=lambda driver: DriverMatcher._distance_km(
                pickup_location,
                driver.location,
            ),
        )

    @staticmethod
    def _distance_km(origin: GeoLocation, destination: GeoLocation) -> float:
        lat1, lon1 = radians(origin.latitude), radians(origin.longitude)
        lat2, lon2 = radians(destination.latitude), radians(destination.longitude)
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        )
        return 2 * EARTH_RADIUS_KM * asin(sqrt(a))

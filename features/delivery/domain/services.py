from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

from features.delivery.domain.constants import DEFAULT_RADIUS_KM
from features.delivery.domain.exceptions import NoDriverAvailableError
from features.stores.domain.value_objects import GeoLocation

EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True, slots=True)
class OnlineDriver:
    driver_id: int
    location: GeoLocation
    work_center: GeoLocation | None = None
    work_radius_km: float = DEFAULT_RADIUS_KM


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
            key=lambda driver: DriverMatcher.distance_km(
                pickup_location,
                driver.location,
            ),
        )

    @staticmethod
    def distance_km(origin: GeoLocation, destination: GeoLocation) -> float:
        lat1, lon1 = radians(origin.latitude), radians(origin.longitude)
        lat2, lon2 = radians(destination.latitude), radians(destination.longitude)
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        )
        return 2 * EARTH_RADIUS_KM * asin(sqrt(a))

    @staticmethod
    def covers_point(
        *,
        point: GeoLocation,
        center: GeoLocation,
        radius_km: float,
    ) -> bool:
        return DriverMatcher.distance_km(center, point) <= radius_km

    @staticmethod
    def driver_covers_store(driver: OnlineDriver, store_location: GeoLocation) -> bool:
        """True si la tienda cae en la zona de trabajo del conductor."""
        if driver.work_center is not None:
            return DriverMatcher.covers_point(
                point=store_location,
                center=driver.work_center,
                radius_km=driver.work_radius_km,
            )
        # Legacy: sin centro configurado → GPS + radio default
        return DriverMatcher.covers_point(
            point=store_location,
            center=driver.location,
            radius_km=DEFAULT_RADIUS_KM,
        )

    # Compat: callers antiguos
    _distance_km = distance_km

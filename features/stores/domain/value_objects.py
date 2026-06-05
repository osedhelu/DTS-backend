from dataclasses import dataclass

from features.stores.domain.exceptions import InvalidGeoLocationError


@dataclass(frozen=True, slots=True)
class GeoLocation:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise InvalidGeoLocationError(
                f"Latitud inválida: {self.latitude}. Debe estar entre -90 y 90."
            )
        if not -180.0 <= self.longitude <= 180.0:
            raise InvalidGeoLocationError(
                f"Longitud inválida: {self.longitude}. Debe estar entre -180 y 180."
            )

    def __str__(self) -> str:
        return f"{self.latitude},{self.longitude}"

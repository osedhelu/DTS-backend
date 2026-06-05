from dataclasses import dataclass, field
from datetime import datetime

from features.delivery.domain.exceptions import InvalidTrackingPointError
from features.stores.domain.exceptions import InvalidGeoLocationError
from features.stores.domain.value_objects import GeoLocation


@dataclass
class TrackingPoint:
    latitude: float
    longitude: float
    sequence: int
    recorded_at: datetime
    id: int | None = None

    def __post_init__(self) -> None:
        if self.sequence <= 0:
            raise InvalidTrackingPointError(
                f"La secuencia debe ser positiva, recibida: {self.sequence}"
            )
        GeoLocation(latitude=self.latitude, longitude=self.longitude)


@dataclass
class DeliveryTracking:
    order_id: int
    points: list[TrackingPoint] = field(default_factory=list)
    id: int | None = None

    def add_point(
        self,
        latitude: float,
        longitude: float,
        recorded_at: datetime,
    ) -> TrackingPoint:
        if self.points and recorded_at < self.points[-1].recorded_at:
            raise InvalidTrackingPointError(
                "Los puntos de tracking deben registrarse en orden cronológico"
            )

        point = TrackingPoint(
            latitude=latitude,
            longitude=longitude,
            sequence=len(self.points) + 1,
            recorded_at=recorded_at,
        )
        self.points.append(point)
        return point

    @property
    def latest_point(self) -> TrackingPoint | None:
        if not self.points:
            return None
        return self.points[-1]

    @property
    def point_count(self) -> int:
        return len(self.points)

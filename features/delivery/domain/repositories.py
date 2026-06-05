from typing import Protocol

from features.delivery.domain.entities import DeliveryTracking
from features.delivery.domain.services import OnlineDriver


class DeliveryTrackingRepository(Protocol):
    def get_by_order_id(self, order_id: int) -> DeliveryTracking | None: ...

    def get_or_create(self, order_id: int) -> DeliveryTracking: ...

    def save(self, tracking: DeliveryTracking) -> DeliveryTracking: ...


class DriverAvailabilityRepository(Protocol):
    def list_online_drivers(self) -> list[OnlineDriver]: ...

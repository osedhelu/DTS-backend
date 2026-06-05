from typing import Protocol

from features.delivery.domain.entities import DeliveryTracking


class DeliveryTrackingRepository(Protocol):
    def get_by_order_id(self, order_id: int) -> DeliveryTracking | None: ...

    def get_or_create(self, order_id: int) -> DeliveryTracking: ...

    def save(self, tracking: DeliveryTracking) -> DeliveryTracking: ...

from features.delivery.application.dto import RecordLocationDTO
from features.delivery.domain.entities import DeliveryTracking
from features.delivery.domain.exceptions import (
    InvalidOrderStatusForTrackingError,
    ServiceOrderNotTrackableError,
    UnauthorizedDriverError,
)
from features.delivery.domain.repositories import DeliveryTrackingRepository
from features.delivery.domain.value_objects import TRACKABLE_ORDER_STATUSES
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.repositories import OrderRepository
from features.orders.domain.value_objects import OrderType


class RecordLocationUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        tracking_repository: DeliveryTrackingRepository,
    ) -> None:
        self._order_repository = order_repository
        self._tracking_repository = tracking_repository

    def execute(self, dto: RecordLocationDTO) -> DeliveryTracking:
        order = self._order_repository.get_by_id(dto.order_id)
        if order is None:
            raise OrderNotFoundError(f"Pedido {dto.order_id} no encontrado")

        if order.order_type != OrderType.DELIVERY:
            raise ServiceOrderNotTrackableError(
                "Solo los pedidos de delivery admiten tracking GPS del conductor"
            )

        if order.driver_id != dto.driver_id:
            raise UnauthorizedDriverError(
                "El conductor no está asignado a este pedido"
            )

        if order.status not in TRACKABLE_ORDER_STATUSES:
            raise InvalidOrderStatusForTrackingError(
                f"El pedido en estado '{order.status}' no admite registro de ubicación"
            )

        tracking = self._tracking_repository.get_or_create(dto.order_id)
        tracking.add_point(dto.latitude, dto.longitude, dto.recorded_at)
        return self._tracking_repository.save(tracking)

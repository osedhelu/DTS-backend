from features.delivery.domain.entities import DeliveryTracking
from features.delivery.domain.exceptions import UnauthorizedTrackingAccessError
from features.delivery.domain.repositories import DeliveryTrackingRepository
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.repositories import OrderRepository


class GetOrderTrackingUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        tracking_repository: DeliveryTrackingRepository,
    ) -> None:
        self._order_repository = order_repository
        self._tracking_repository = tracking_repository

    def execute(self, order_id: int, customer_id: int) -> DeliveryTracking:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Pedido {order_id} no encontrado")

        if order.customer_id != customer_id:
            raise UnauthorizedTrackingAccessError(
                "No tienes permiso para ver el tracking de este pedido"
            )

        tracking = self._tracking_repository.get_by_order_id(order_id)
        if tracking is None:
            return DeliveryTracking(order_id=order_id)
        return tracking

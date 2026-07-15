from features.delivery.domain.entities import DeliveryTracking
from features.delivery.domain.exceptions import UnauthorizedTrackingAccessError
from features.delivery.domain.repositories import DeliveryTrackingRepository
from features.delivery.domain.value_objects import TRACKABLE_ORDER_STATUSES
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.repositories import OrderRepository
from features.stores.domain.repositories import StoreRepository


class GetOrderTrackingUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        tracking_repository: DeliveryTrackingRepository,
        store_repository: StoreRepository | None = None,
    ) -> None:
        self._order_repository = order_repository
        self._tracking_repository = tracking_repository
        self._store_repository = store_repository

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
            tracking = DeliveryTracking(order_id=order_id)

        tracking.order_status = order.status.value
        tracking.is_live = order.status in TRACKABLE_ORDER_STATUSES

        dest_lat = None
        dest_lng = None
        if order.service_details and order.service_details.latitude is not None:
            dest_lat = order.service_details.latitude
            dest_lng = order.service_details.longitude
        elif self._store_repository is not None:
            store = self._store_repository.get_by_id(order.store_id)
            if store is not None:
                dest_lat = store.latitude
                dest_lng = store.longitude

        tracking.destination_latitude = dest_lat
        tracking.destination_longitude = dest_lng
        return tracking

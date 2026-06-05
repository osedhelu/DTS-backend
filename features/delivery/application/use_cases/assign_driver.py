from features.delivery.domain.exceptions import InvalidOrderForDriverAssignmentError
from features.delivery.domain.repositories import DriverAvailabilityRepository
from features.delivery.domain.services import DriverMatcher
from features.delivery.domain.value_objects import ASSIGNABLE_ORDER_STATUSES
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.repositories import OrderRepository
from features.orders.domain.value_objects import OrderType
from features.stores.domain.repositories import StoreRepository
from features.stores.domain.value_objects import GeoLocation


class AssignDriverUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        store_repository: StoreRepository,
        driver_availability_repository: DriverAvailabilityRepository,
    ) -> None:
        self._order_repository = order_repository
        self._store_repository = store_repository
        self._driver_availability_repository = driver_availability_repository

    def execute(self, order_id: int) -> int:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Pedido {order_id} no encontrado")

        if order.driver_id is not None:
            return order.driver_id

        if order.order_type != OrderType.DELIVERY:
            raise InvalidOrderForDriverAssignmentError(
                "Solo los pedidos de delivery admiten asignación de conductor"
            )

        if order.status not in ASSIGNABLE_ORDER_STATUSES:
            raise InvalidOrderForDriverAssignmentError(
                f"El pedido en estado '{order.status}' no admite asignación de conductor"
            )

        store = self._store_repository.get_by_id(order.store_id)
        if store is None:
            raise OrderNotFoundError(f"Comercio {order.store_id} no encontrado")

        pickup_location = GeoLocation(latitude=store.latitude, longitude=store.longitude)
        online_drivers = self._driver_availability_repository.list_online_drivers()
        nearest = DriverMatcher.find_nearest_driver(pickup_location, online_drivers)

        updated_order = self._order_repository.assign_driver(order_id, nearest.driver_id)
        return updated_order.driver_id

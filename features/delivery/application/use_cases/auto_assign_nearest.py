from datetime import timedelta

from django.utils import timezone

from features.delivery.domain.exceptions import NoDriverAvailableError
from features.delivery.domain.repositories import DriverAvailabilityRepository
from features.delivery.domain.services import DriverMatcher
from features.orders.domain.repositories import OrderRepository
from features.orders.domain.services import OrderStateMachine
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.orders.infrastructure.models import Order as OrderModel
from features.stores.domain.repositories import StoreRepository
from features.stores.domain.value_objects import GeoLocation


class AutoAssignNearestUseCase:
    """Fallback Beat: asigna el conductor más cercano a pedidos stale en búsqueda."""

    def __init__(
        self,
        order_repository: OrderRepository,
        store_repository: StoreRepository,
        driver_availability_repository: DriverAvailabilityRepository,
    ) -> None:
        self._order_repository = order_repository
        self._store_repository = store_repository
        self._driver_availability_repository = driver_availability_repository

    def execute(self, *, stale_minutes: int = 3) -> list[int]:
        cutoff = timezone.now() - timedelta(minutes=stale_minutes)
        stale = OrderModel.objects.filter(
            status=OrderStatus.SEARCHING_DRIVER,
            order_type=OrderType.DELIVERY,
            driver__isnull=True,
            updated_at__lte=cutoff,
        ).order_by("updated_at")[:20]

        assigned: list[int] = []
        for order in stale:
            try:
                driver_id = self._assign_one(order.id, order.store_id)
            except NoDriverAvailableError:
                continue
            assigned.append(order.id)
            _ = driver_id
        return assigned

    def _assign_one(self, order_id: int, store_id: int) -> int:
        store = self._store_repository.get_by_id(store_id)
        if store is None:
            raise NoDriverAvailableError("Comercio no encontrado")

        pickup = GeoLocation(latitude=store.latitude, longitude=store.longitude)
        online = self._driver_availability_repository.list_online_drivers()
        nearest = DriverMatcher.find_nearest_driver(pickup, online)

        self._order_repository.assign_driver(order_id, nearest.driver_id)
        OrderStateMachine.transition(
            OrderStatus.SEARCHING_DRIVER, OrderStatus.DRIVER_ASSIGNED
        )
        self._order_repository.update_status(order_id, OrderStatus.DRIVER_ASSIGNED)
        return nearest.driver_id

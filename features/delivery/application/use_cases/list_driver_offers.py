from dataclasses import dataclass

from features.delivery.domain.constants import MAX_DRIVER_OFFER_DISTANCE_KM
from features.delivery.domain.exceptions import DriverProfileNotFoundForOffersError
from features.delivery.domain.services import DriverMatcher
from features.delivery.infrastructure.models import DriverOfferRejection
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.orders.infrastructure.models import Order as OrderModel
from features.accounts.infrastructure.models import DriverProfile
from features.stores.domain.value_objects import GeoLocation
from features.stores.infrastructure.models import Store


@dataclass(frozen=True, slots=True)
class DriverOfferItem:
    order_id: int
    store_id: int
    store_name: str
    store_latitude: float
    store_longitude: float
    total: str
    distance_km: float
    status: str


class ListDriverOffersUseCase:
    """Lista pedidos SEARCHING_DRIVER cercanos, excluyendo rechazos del conductor."""

    MAX_DISTANCE_KM = MAX_DRIVER_OFFER_DISTANCE_KM

    def execute(self, driver_id: int) -> list[DriverOfferItem]:
        try:
            profile = DriverProfile.objects.get(user_id=driver_id)
        except DriverProfile.DoesNotExist as exc:
            raise DriverProfileNotFoundForOffersError(
                "El conductor no tiene perfil configurado"
            ) from exc

        if not profile.has_last_location:
            return []

        driver_location = GeoLocation(
            latitude=profile.last_latitude,
            longitude=profile.last_longitude,
        )

        rejected_ids = set(
            DriverOfferRejection.objects.filter(driver_id=driver_id).values_list(
                "order_id", flat=True
            )
        )

        orders = (
            OrderModel.objects.filter(
                status=OrderStatus.SEARCHING_DRIVER,
                order_type=OrderType.DELIVERY,
                driver__isnull=True,
            )
            .select_related("store")
            .order_by("-created_at")[:50]
        )

        offers: list[DriverOfferItem] = []
        for order in orders:
            if order.id in rejected_ids:
                continue
            store: Store = order.store
            store_location = GeoLocation(
                latitude=store.latitude, longitude=store.longitude
            )
            distance = DriverMatcher.distance_km(driver_location, store_location)
            if distance > self.MAX_DISTANCE_KM:
                continue
            offers.append(
                DriverOfferItem(
                    order_id=order.id,
                    store_id=store.id,
                    store_name=store.name,
                    store_latitude=store.latitude,
                    store_longitude=store.longitude,
                    total=str(order.total),
                    distance_km=round(distance, 2),
                    status=order.status,
                )
            )

        offers.sort(key=lambda item: item.distance_km)
        return offers

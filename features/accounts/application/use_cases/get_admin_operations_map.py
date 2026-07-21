from dataclasses import dataclass
from datetime import datetime

from features.accounts.infrastructure.models import DriverProfile
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.orders.infrastructure.models import Order
from features.stores.infrastructure.models import Store

ACTIVE_DELIVERY_STATUSES = [
    OrderStatus.ACCEPTED_BY_MERCHANT.value,
    OrderStatus.IN_PREPARATION.value,
    OrderStatus.READY_FOR_PICKUP.value,
    OrderStatus.SEARCHING_DRIVER.value,
    OrderStatus.DRIVER_ASSIGNED.value,
    OrderStatus.PICKED_UP.value,
    OrderStatus.ON_THE_WAY.value,
]


@dataclass(frozen=True)
class AdminMapStoreRow:
    id: int
    name: str
    latitude: float
    longitude: float
    is_active: bool
    vertical: str
    address: str


@dataclass(frozen=True)
class AdminMapDeliveryRow:
    order_id: int
    status: str
    order_type: str
    store_id: int
    store_name: str
    store_latitude: float
    store_longitude: float
    driver_id: int | None
    destination_latitude: float | None
    destination_longitude: float | None
    destination_label: str
    latest_latitude: float | None
    latest_longitude: float | None
    latest_recorded_at: datetime | None
    gps_source: str | None = None


@dataclass(frozen=True)
class AdminMapOnlineDriverRow:
    driver_id: int
    full_name: str
    latitude: float
    longitude: float
    updated_at: datetime | None


@dataclass(frozen=True)
class AdminOperationsMapData:
    stores: list[AdminMapStoreRow]
    active_deliveries: list[AdminMapDeliveryRow]
    online_drivers: list[AdminMapOnlineDriverRow]


class GetAdminOperationsMapUseCase:
    def execute(self, *, owner_id: int | None = None) -> AdminOperationsMapData:
        store_qs = Store.objects.all().order_by("name")
        if owner_id is not None:
            store_qs = store_qs.filter(owner_id=owner_id)

        stores = [
            AdminMapStoreRow(
                id=store.id,
                name=store.name,
                latitude=store.latitude,
                longitude=store.longitude,
                is_active=store.is_active,
                vertical=store.vertical,
                address=store.address or "",
            )
            for store in store_qs
        ]

        store_ids = [store.id for store in stores]

        orders = (
            Order.objects.filter(
                order_type=OrderType.DELIVERY.value,
                status__in=ACTIVE_DELIVERY_STATUSES,
                store_id__in=store_ids,
            )
            if store_ids
            else Order.objects.none()
        )
        orders = (
            orders.select_related("store", "delivery_tracking")
            .prefetch_related("delivery_tracking__points")
            .order_by("-updated_at")
        )

        driver_ids = [
            order.driver_id for order in orders if order.driver_id is not None
        ]
        driver_profiles = {
            profile.user_id: profile
            for profile in DriverProfile.objects.filter(user_id__in=driver_ids)
        }

        deliveries: list[AdminMapDeliveryRow] = []
        for order in orders:
            store = order.store
            tracking = getattr(order, "delivery_tracking", None)
            latest_point = None
            if tracking is not None and tracking.points.exists():
                latest_point = max(tracking.points.all(), key=lambda point: point.sequence)

            latest_latitude = latest_point.latitude if latest_point else None
            latest_longitude = latest_point.longitude if latest_point else None
            latest_recorded_at = latest_point.recorded_at if latest_point else None
            gps_source = "tracking" if latest_point else None

            if latest_point is None and order.driver_id is not None:
                profile = driver_profiles.get(order.driver_id)
                if profile is not None and profile.has_last_location:
                    latest_latitude = profile.last_latitude
                    latest_longitude = profile.last_longitude
                    latest_recorded_at = profile.updated_at
                    gps_source = "profile"

            deliveries.append(
                AdminMapDeliveryRow(
                    order_id=order.id,
                    status=order.status,
                    order_type=order.order_type,
                    store_id=store.id,
                    store_name=store.name,
                    store_latitude=store.latitude,
                    store_longitude=store.longitude,
                    driver_id=order.driver_id,
                    destination_latitude=order.service_latitude,
                    destination_longitude=order.service_longitude,
                    destination_label=order.service_address or "",
                    latest_latitude=latest_latitude,
                    latest_longitude=latest_longitude,
                    latest_recorded_at=latest_recorded_at,
                    gps_source=gps_source,
                )
            )

        online_qs = DriverProfile.objects.filter(
            is_online=True,
            last_latitude__isnull=False,
            last_longitude__isnull=False,
        ).select_related("user")

        assigned_driver_ids = {
            delivery.driver_id
            for delivery in deliveries
            if delivery.driver_id is not None
        }

        online_drivers = [
            AdminMapOnlineDriverRow(
                driver_id=profile.user_id,
                full_name=profile.user.get_full_name() or profile.user.username,
                latitude=profile.last_latitude,
                longitude=profile.last_longitude,
                updated_at=profile.updated_at,
            )
            for profile in online_qs
            if profile.user_id not in assigned_driver_ids
        ]

        return AdminOperationsMapData(
            stores=stores,
            active_deliveries=deliveries,
            online_drivers=online_drivers,
        )

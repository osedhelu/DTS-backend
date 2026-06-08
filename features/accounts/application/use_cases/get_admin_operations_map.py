from dataclasses import dataclass
from datetime import datetime

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


@dataclass(frozen=True)
class AdminOperationsMapData:
    stores: list[AdminMapStoreRow]
    active_deliveries: list[AdminMapDeliveryRow]


class GetAdminOperationsMapUseCase:
    def execute(self) -> AdminOperationsMapData:
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
            for store in Store.objects.all().order_by("name")
        ]

        orders = (
            Order.objects.filter(
                order_type=OrderType.DELIVERY.value,
                status__in=ACTIVE_DELIVERY_STATUSES,
            )
            .select_related("store", "delivery_tracking")
            .prefetch_related("delivery_tracking__points")
            .order_by("-updated_at")
        )

        deliveries: list[AdminMapDeliveryRow] = []
        for order in orders:
            store = order.store
            tracking = getattr(order, "delivery_tracking", None)
            latest_point = None
            if tracking is not None and tracking.points.exists():
                latest_point = max(tracking.points.all(), key=lambda point: point.sequence)

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
                    latest_latitude=latest_point.latitude if latest_point else None,
                    latest_longitude=latest_point.longitude if latest_point else None,
                    latest_recorded_at=latest_point.recorded_at if latest_point else None,
                )
            )

        return AdminOperationsMapData(stores=stores, active_deliveries=deliveries)

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from features.orders.domain.exceptions import InvalidServiceOrderDetailsError


class OrderType(StrEnum):
    DELIVERY = "delivery"
    SERVICE = "service"


class OrderStatus(StrEnum):
    """Estados de un pedido en la plataforma (delivery y servicios a domicilio)."""

    # Compartidos
    CREATED = "created"
    ACCEPTED_BY_MERCHANT = "accepted_by_merchant"
    CANCELLED = "cancelled"

    # Delivery — productos físicos con conductor
    IN_PREPARATION = "in_preparation"
    READY_FOR_PICKUP = "ready_for_pickup"
    SEARCHING_DRIVER = "searching_driver"
    DRIVER_ASSIGNED = "driver_assigned"
    PICKED_UP = "picked_up"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"

    # Servicio — visita a domicilio sin conductor de plataforma
    SCHEDULED = "scheduled"
    PROVIDER_EN_ROUTE = "provider_en_route"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


DELIVERY_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.CREATED,
        OrderStatus.ACCEPTED_BY_MERCHANT,
        OrderStatus.IN_PREPARATION,
        OrderStatus.READY_FOR_PICKUP,
        OrderStatus.SEARCHING_DRIVER,
        OrderStatus.DRIVER_ASSIGNED,
        OrderStatus.PICKED_UP,
        OrderStatus.ON_THE_WAY,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    }
)

SERVICE_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.CREATED,
        OrderStatus.ACCEPTED_BY_MERCHANT,
        OrderStatus.SCHEDULED,
        OrderStatus.PROVIDER_EN_ROUTE,
        OrderStatus.IN_PROGRESS,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    }
)

TERMINAL_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.DELIVERED,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    }
)


@dataclass(frozen=True, slots=True)
class ServiceOrderDetails:
    """Datos adicionales para pedidos de servicio a domicilio."""

    service_address: str
    customer_notes: str = ""
    scheduled_at: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    duration_minutes: int | None = None

    def __post_init__(self) -> None:
        if not self.service_address.strip():
            raise InvalidServiceOrderDetailsError(
                "La dirección del servicio es obligatoria"
            )

        has_latitude = self.latitude is not None
        has_longitude = self.longitude is not None
        if has_latitude ^ has_longitude:
            raise InvalidServiceOrderDetailsError(
                "Debe indicar latitud y longitud juntas o ninguna"
            )

        if has_latitude and has_longitude:
            if not -90.0 <= self.latitude <= 90.0:
                raise InvalidServiceOrderDetailsError(
                    f"Latitud inválida: {self.latitude}"
                )
            if not -180.0 <= self.longitude <= 180.0:
                raise InvalidServiceOrderDetailsError(
                    f"Longitud inválida: {self.longitude}"
                )

        if self.duration_minutes is not None and self.duration_minutes <= 0:
            raise InvalidServiceOrderDetailsError(
                "La duración estimada debe ser positiva"
            )

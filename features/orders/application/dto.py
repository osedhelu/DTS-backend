from dataclasses import dataclass
from datetime import datetime

from features.accounts.domain.entities import UserRole
from features.orders.domain.value_objects import OrderStatus


@dataclass(frozen=True)
class OrderLineDTO:
    product_id: int
    quantity: int


@dataclass(frozen=True)
class CreateOrderDTO:
    customer_id: int
    store_id: int
    items: tuple[OrderLineDTO, ...]


@dataclass(frozen=True)
class CreateServiceOrderDTO:
    customer_id: int
    store_id: int
    items: tuple[OrderLineDTO, ...]
    service_address: str
    customer_notes: str = ""
    scheduled_at: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class TransitionOrderStatusDTO:
    order_id: int
    target_status: OrderStatus
    actor_id: int
    actor_role: UserRole

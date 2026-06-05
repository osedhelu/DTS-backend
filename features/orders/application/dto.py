from dataclasses import dataclass

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
class TransitionOrderStatusDTO:
    order_id: int
    target_status: OrderStatus
    actor_id: int
    actor_role: UserRole

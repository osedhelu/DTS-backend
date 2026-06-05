from typing import Any, Protocol

from features.orders.domain.entities import Order
from features.orders.domain.value_objects import OrderStatus


class OrderRepository(Protocol):
    def create(self, data: dict[str, Any]) -> Order: ...

    def get_by_id(self, order_id: int) -> Order | None: ...

    def update_status(self, order_id: int, status: OrderStatus) -> Order: ...

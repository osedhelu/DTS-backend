from dataclasses import dataclass

from features.orders.domain.value_objects import OrderStatus


@dataclass(frozen=True, slots=True)
class SendPushDTO:
    user_id: int
    order_id: int
    order_status: OrderStatus

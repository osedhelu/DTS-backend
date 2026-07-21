from dataclasses import dataclass

from features.orders.domain.value_objects import OrderStatus


@dataclass(frozen=True, slots=True)
class SendPushDTO:
    user_id: int
    order_id: int
    order_status: OrderStatus
    title_override: str | None = None
    body_override: str | None = None


@dataclass(frozen=True, slots=True)
class SendChatPushDTO:
    user_id: int
    order_id: int
    preview: str
    sender_role: str = ""

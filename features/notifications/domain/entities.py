from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from features.notifications.domain.exceptions import PushTemplateNotFoundError
from features.orders.domain.value_objects import OrderStatus


class NotificationType(StrEnum):
    """Tipos de notificación push soportados por la plataforma."""

    ORDER_ACCEPTED = "order_accepted"
    ORDER_IN_PREPARATION = "order_in_preparation"
    NEW_ORDER_READY_FOR_PICKUP = "new_order_ready_for_pickup"
    DRIVER_ASSIGNED = "driver_assigned"
    ORDER_PICKED_UP = "order_picked_up"
    ORDER_ON_THE_WAY = "order_on_the_way"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"


@dataclass(frozen=True, slots=True)
class PushTemplate:
    notification_type: NotificationType
    title: str
    body: str

    _BY_STATUS: ClassVar[dict[OrderStatus, "PushTemplate"] | None] = None

    @classmethod
    def for_status(cls, status: OrderStatus) -> "PushTemplate":
        template = cls._templates_by_status().get(status)
        if template is None:
            raise PushTemplateNotFoundError(
                f"No hay plantilla push para el estado '{status}'"
            )
        return template

    @classmethod
    def _templates_by_status(cls) -> dict[OrderStatus, "PushTemplate"]:
        if cls._BY_STATUS is None:
            cls._BY_STATUS = {
                OrderStatus.ACCEPTED_BY_MERCHANT: cls(
                    notification_type=NotificationType.ORDER_ACCEPTED,
                    title="Pedido aceptado",
                    body="Tu pedido fue aceptado",
                ),
                OrderStatus.IN_PREPARATION: cls(
                    notification_type=NotificationType.ORDER_IN_PREPARATION,
                    title="En preparación",
                    body="Estamos preparando tu pedido",
                ),
                OrderStatus.READY_FOR_PICKUP: cls(
                    notification_type=NotificationType.NEW_ORDER_READY_FOR_PICKUP,
                    title="Nuevo pedido",
                    body="Nuevo pedido listo para recoger",
                ),
                OrderStatus.DRIVER_ASSIGNED: cls(
                    notification_type=NotificationType.DRIVER_ASSIGNED,
                    title="Conductor asignado",
                    body="Conductor asignado a tu pedido",
                ),
                OrderStatus.PICKED_UP: cls(
                    notification_type=NotificationType.ORDER_PICKED_UP,
                    title="Pedido recogido",
                    body="El conductor recogió tu pedido",
                ),
                OrderStatus.ON_THE_WAY: cls(
                    notification_type=NotificationType.ORDER_ON_THE_WAY,
                    title="Pedido en camino",
                    body="¡Tu pedido ya salió! Va en camino",
                ),
                OrderStatus.DELIVERED: cls(
                    notification_type=NotificationType.ORDER_DELIVERED,
                    title="Pedido entregado",
                    body="Pedido entregado. ¡Buen provecho!",
                ),
                OrderStatus.CANCELLED: cls(
                    notification_type=NotificationType.ORDER_CANCELLED,
                    title="Pedido cancelado",
                    body="Tu pedido fue cancelado",
                ),
            }
        return cls._BY_STATUS

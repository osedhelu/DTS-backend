from django.db import transaction
from django.utils import timezone

from features.delivery.domain.exceptions import (
    OfferAlreadyTakenError,
    OfferNotAcceptableError,
)
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.services import OrderStateMachine
from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.models import Order as OrderModel


class AcceptOfferUseCase:
    """First-wins: asigna el pedido al conductor con select_for_update."""

    def execute(self, order_id: int, driver_id: int) -> int:
        with transaction.atomic():
            try:
                model = (
                    OrderModel.objects.select_for_update()
                    .prefetch_related("items")
                    .get(pk=order_id)
                )
            except OrderModel.DoesNotExist as exc:
                raise OrderNotFoundError(f"Pedido {order_id} no encontrado") from exc

            if model.driver_id is not None:
                raise OfferAlreadyTakenError("Otro conductor ya aceptó este pedido")

            if model.status != OrderStatus.SEARCHING_DRIVER:
                raise OfferNotAcceptableError(
                    f"El pedido en estado '{model.status}' no admite aceptación"
                )

            OrderStateMachine.transition(
                OrderStatus.SEARCHING_DRIVER, OrderStatus.DRIVER_ASSIGNED
            )
            model.driver_id = driver_id
            model.status = OrderStatus.DRIVER_ASSIGNED
            model.updated_at = timezone.now()
            model.save(update_fields=["driver_id", "status", "updated_at"])

        return driver_id

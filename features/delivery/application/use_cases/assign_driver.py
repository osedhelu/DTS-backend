from features.delivery.domain.exceptions import InvalidOrderForDriverAssignmentError
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.repositories import OrderRepository
from features.orders.domain.services import OrderStateMachine
from features.orders.domain.value_objects import OrderStatus, OrderType


class AssignDriverUseCase:
    """Abre la búsqueda de conductor (SEARCHING_DRIVER) sin auto-asignar."""

    def __init__(
        self,
        order_repository: OrderRepository,
        store_repository=None,
        driver_availability_repository=None,
    ) -> None:
        # store/availability se mantienen en la firma por compatibilidad con
        # el wiring existente de la task Celery; ya no se usan aquí.
        self._order_repository = order_repository

    def execute(self, order_id: int) -> int | None:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Pedido {order_id} no encontrado")

        if order.driver_id is not None:
            return order.driver_id

        if order.order_type != OrderType.DELIVERY:
            raise InvalidOrderForDriverAssignmentError(
                "Solo los pedidos de delivery admiten asignación de conductor"
            )

        if order.status == OrderStatus.SEARCHING_DRIVER:
            return None

        if order.status != OrderStatus.READY_FOR_PICKUP:
            raise InvalidOrderForDriverAssignmentError(
                f"El pedido en estado '{order.status}' no admite asignación de conductor"
            )

        OrderStateMachine.transition(order.status, OrderStatus.SEARCHING_DRIVER)
        self._order_repository.update_status(order_id, OrderStatus.SEARCHING_DRIVER)
        return None

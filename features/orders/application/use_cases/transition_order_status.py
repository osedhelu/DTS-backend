from features.accounts.domain.entities import UserRole
from features.orders.application.dto import TransitionOrderStatusDTO
from features.orders.domain.exceptions import (
    OrderNotFoundError,
    UnauthorizedOrderTransitionError,
)
from features.orders.domain.repositories import OrderRepository
from features.orders.domain.services import OrderStateMachine, ServiceOrderStateMachine
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.domain.repositories import StoreRepository

MERCHANT_TARGET_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.ACCEPTED_BY_MERCHANT,
        OrderStatus.IN_PREPARATION,
        OrderStatus.READY_FOR_PICKUP,
        OrderStatus.SEARCHING_DRIVER,
        OrderStatus.CANCELLED,
    }
)

MERCHANT_SERVICE_TARGET_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.ACCEPTED_BY_MERCHANT,
        OrderStatus.SCHEDULED,
        OrderStatus.PROVIDER_EN_ROUTE,
        OrderStatus.IN_PROGRESS,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    }
)

DRIVER_TARGET_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.PICKED_UP,
        OrderStatus.ON_THE_WAY,
        OrderStatus.DELIVERED,
    }
)

CUSTOMER_TARGET_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.CANCELLED,
    }
)


class TransitionOrderStatusUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._order_repository = order_repository
        self._store_repository = store_repository

    def execute(self, dto: TransitionOrderStatusDTO):
        order = self._order_repository.get_by_id(dto.order_id)
        if order is None:
            raise OrderNotFoundError(f"Pedido {dto.order_id} no encontrado")

        self._authorize_transition(order, dto)

        if order.order_type == OrderType.SERVICE:
            ServiceOrderStateMachine.transition(order.status, dto.target_status)
        else:
            OrderStateMachine.transition(order.status, dto.target_status)

        return self._order_repository.update_status(dto.order_id, dto.target_status)

    def _authorize_transition(self, order, dto: TransitionOrderStatusDTO) -> None:
        if dto.actor_role == UserRole.MERCHANT:
            self._ensure_merchant_owns_store(order.store_id, dto.actor_id)
            allowed_targets = (
                MERCHANT_SERVICE_TARGET_STATUSES
                if order.order_type == OrderType.SERVICE
                else MERCHANT_TARGET_STATUSES
            )
            if dto.target_status not in allowed_targets:
                raise UnauthorizedOrderTransitionError(
                    "El comercio no puede aplicar este estado al pedido"
                )
            return

        if dto.actor_role == UserRole.CUSTOMER:
            if order.customer_id != dto.actor_id:
                raise UnauthorizedOrderTransitionError(
                    "No tienes permiso para modificar este pedido"
                )
            if dto.target_status not in CUSTOMER_TARGET_STATUSES:
                raise UnauthorizedOrderTransitionError(
                    "El cliente no puede aplicar este estado al pedido"
                )
            return

        if dto.actor_role == UserRole.DRIVER:
            if order.driver_id != dto.actor_id:
                raise UnauthorizedOrderTransitionError(
                    "No tienes permiso para modificar este pedido"
                )
            if dto.target_status not in DRIVER_TARGET_STATUSES:
                raise UnauthorizedOrderTransitionError(
                    "El conductor no puede aplicar este estado al pedido"
                )
            return

        raise UnauthorizedOrderTransitionError(
            f"El rol '{dto.actor_role}' no puede cambiar el estado del pedido"
        )

    def _ensure_merchant_owns_store(self, store_id: int, owner_id: int) -> None:
        store = self._store_repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {store_id} no encontrado")
        if store.owner_id != owner_id:
            raise NotStoreOwnerError("No tienes permiso para modificar pedidos de este comercio")

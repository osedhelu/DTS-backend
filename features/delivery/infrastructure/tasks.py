from celery import shared_task

from features.delivery.application.use_cases.assign_driver import AssignDriverUseCase
from features.delivery.application.use_cases.auto_assign_nearest import (
    AutoAssignNearestUseCase,
)
from features.delivery.infrastructure.repositories import DjangoDriverAvailabilityRepository
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.infrastructure.repositories import DjangoOrderRepository
from features.stores.infrastructure.repositories import DjangoStoreRepository


def _build_assign_driver_use_case() -> AssignDriverUseCase:
    return AssignDriverUseCase(
        order_repository=DjangoOrderRepository(),
        store_repository=DjangoStoreRepository(),
        driver_availability_repository=DjangoDriverAvailabilityRepository(),
    )


def _build_auto_assign_use_case() -> AutoAssignNearestUseCase:
    return AutoAssignNearestUseCase(
        order_repository=DjangoOrderRepository(),
        store_repository=DjangoStoreRepository(),
        driver_availability_repository=DjangoDriverAvailabilityRepository(),
    )


@shared_task(
    bind=True,
    name="features.delivery.infrastructure.tasks.assign_driver_task",
)
def assign_driver_task(self, order_id: int) -> str:
    """Abre SEARCHING_DRIVER; la asignación ocurre por accept o Beat fallback."""
    use_case = _build_assign_driver_use_case()

    try:
        driver_id = use_case.execute(order_id)
    except OrderNotFoundError:
        return f"not_found:{order_id}"

    if driver_id is not None:
        return f"already_assigned:{order_id}:{driver_id}"
    return f"searching:{order_id}"


@shared_task(
    name="features.delivery.infrastructure.tasks.auto_assign_stale_orders_task",
)
def auto_assign_stale_orders_task(stale_minutes: int = 3) -> str:
    assigned = _build_auto_assign_use_case().execute(stale_minutes=stale_minutes)
    return f"auto_assigned:{len(assigned)}:{','.join(str(i) for i in assigned)}"

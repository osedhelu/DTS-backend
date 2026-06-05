from celery import shared_task

from features.delivery.application.use_cases.assign_driver import AssignDriverUseCase
from features.delivery.domain.exceptions import NoDriverAvailableError
from features.delivery.infrastructure.repositories import DjangoDriverAvailabilityRepository
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.infrastructure.repositories import DjangoOrderRepository
from features.stores.infrastructure.repositories import DjangoStoreRepository

RETRY_COUNTDOWN_SECONDS = 30


def _build_assign_driver_use_case() -> AssignDriverUseCase:
    return AssignDriverUseCase(
        order_repository=DjangoOrderRepository(),
        store_repository=DjangoStoreRepository(),
        driver_availability_repository=DjangoDriverAvailabilityRepository(),
    )


@shared_task(
    bind=True,
    max_retries=3,
    name="features.delivery.infrastructure.tasks.assign_driver_task",
)
def assign_driver_task(self, order_id: int) -> str:
    use_case = _build_assign_driver_use_case()

    try:
        driver_id = use_case.execute(order_id)
    except NoDriverAvailableError as exc:
        raise self.retry(exc=exc, countdown=RETRY_COUNTDOWN_SECONDS) from exc
    except OrderNotFoundError:
        return f"not_found:{order_id}"

    return f"assigned:{order_id}:{driver_id}"

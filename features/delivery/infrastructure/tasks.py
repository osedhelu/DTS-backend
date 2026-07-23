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

    # #region agent log
    try:
        import json
        import logging
        import time
        from pathlib import Path

        logging.getLogger(__name__).info(
            "debug_assign_driver_task_start order_id=%s", order_id
        )
        Path("/tmp/debug-7aed00.log").open("a").write(
            json.dumps(
                {
                    "sessionId": "7aed00",
                    "hypothesisId": "E",
                    "location": "tasks.py:assign_driver_task",
                    "message": "assign_driver_task start",
                    "data": {"order_id": order_id},
                    "timestamp": int(time.time() * 1000),
                    "runId": "prod-diag",
                }
            )
            + "\n"
        )
    except Exception:
        pass
    # #endregion

    try:
        driver_id = use_case.execute(order_id)
    except OrderNotFoundError:
        return f"not_found:{order_id}"
    except Exception as exc:
        # #region agent log
        try:
            import logging

            logging.getLogger(__name__).exception(
                "debug_assign_driver_task_error order_id=%s err=%s",
                order_id,
                exc,
            )
        except Exception:
            pass
        # #endregion
        raise

    result = (
        f"already_assigned:{order_id}:{driver_id}"
        if driver_id is not None
        else f"searching:{order_id}"
    )
    # #region agent log
    try:
        import json
        import logging
        import time
        from pathlib import Path

        logging.getLogger(__name__).info(
            "debug_assign_driver_task_done order_id=%s result=%s",
            order_id,
            result,
        )
        Path("/tmp/debug-7aed00.log").open("a").write(
            json.dumps(
                {
                    "sessionId": "7aed00",
                    "hypothesisId": "E",
                    "location": "tasks.py:assign_driver_task:done",
                    "message": "assign_driver_task done",
                    "data": {"order_id": order_id, "result": result},
                    "timestamp": int(time.time() * 1000),
                    "runId": "prod-diag",
                }
            )
            + "\n"
        )
    except Exception:
        pass
    # #endregion
    return result


@shared_task(
    name="features.delivery.infrastructure.tasks.auto_assign_stale_orders_task",
)
def auto_assign_stale_orders_task(stale_minutes: int = 3) -> str:
    assigned = _build_auto_assign_use_case().execute(stale_minutes=stale_minutes)
    return f"auto_assigned:{len(assigned)}:{','.join(str(i) for i in assigned)}"

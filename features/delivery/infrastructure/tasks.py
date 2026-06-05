from celery import shared_task


@shared_task(
    bind=True,
    max_retries=3,
    name="features.delivery.infrastructure.tasks.assign_driver_task",
)
def assign_driver_task(self, order_id: int) -> str:
    """Stub — lógica de asignación de conductor en T2.3.2."""
    return f"pending:{order_id}"

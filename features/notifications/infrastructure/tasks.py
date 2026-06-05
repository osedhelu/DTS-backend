from celery import shared_task


@shared_task(
    bind=True,
    max_retries=3,
    name="features.notifications.infrastructure.tasks.notify_customer_task",
)
def notify_customer_task(self, order_id: int) -> str:
    """Stub — notificación al cliente en T2.4.x."""
    return f"pending:{order_id}"

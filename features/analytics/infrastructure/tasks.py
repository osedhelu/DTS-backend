from celery import shared_task


@shared_task(name="features.analytics.infrastructure.tasks.calculate_daily_stats")
def calculate_daily_stats() -> str:
    """Stub — lógica de agregación nocturna en T2.5.3."""
    return "pending"

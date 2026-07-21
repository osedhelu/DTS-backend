"""Programación base de Celery Beat."""

from celery.schedules import crontab

BEAT_SCHEDULE = {
    "nightly-stats": {
        "task": "features.analytics.infrastructure.tasks.calculate_daily_stats",
        "schedule": crontab(hour=2, minute=0),
    },
    "auto-assign-stale-orders": {
        "task": "features.delivery.infrastructure.tasks.auto_assign_stale_orders_task",
        "schedule": 60.0,  # cada 60s
    },
    "sync-store-hours": {
        "task": "features.stores.infrastructure.tasks.sync_store_hours_task",
        "schedule": 900.0,  # cada 15 min
    },
}

"""Programación base de Celery Beat."""

from celery.schedules import crontab

BEAT_SCHEDULE = {
    "nightly-stats": {
        "task": "features.analytics.infrastructure.tasks.calculate_daily_stats",
        "schedule": crontab(hour=2, minute=0),
    },
}

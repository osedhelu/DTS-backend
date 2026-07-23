"""Aplicación Celery — broker Redis, workers para tareas asíncronas."""

import os

from celery import Celery

from core.beat_schedule import BEAT_SCHEDULE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("dts")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.beat_schedule = BEAT_SCHEDULE
# Tasks viven en features/*/infrastructure/tasks.py (no en features/*/tasks.py)
app.autodiscover_tasks(related_name="infrastructure.tasks")
# Registro explícito por si autodiscover falla en algún entorno
app.conf.imports = (
    "features.accounts.infrastructure.tasks",
    "features.analytics.infrastructure.tasks",
    "features.delivery.infrastructure.tasks",
    "features.notifications.infrastructure.tasks",
    "features.stores.infrastructure.tasks",
)

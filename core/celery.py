"""Aplicación Celery — broker Redis, workers para tareas asíncronas."""

import os

from celery import Celery

from core.beat_schedule import BEAT_SCHEDULE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("dts")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.beat_schedule = BEAT_SCHEDULE
app.autodiscover_tasks()

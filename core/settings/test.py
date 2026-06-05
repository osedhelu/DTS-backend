"""Settings para pytest."""
from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-secret-key"

from core.settings.apps_registry import build_installed_apps

# Sin django.contrib.gis en tests (evita dependencia GDAL del sistema)
INSTALLED_APPS = [
    app for app in build_installed_apps(BASE_DIR) if app != "django.contrib.gis"  # noqa: F405
]

# Tests usan SQLite en memoria (sin PostGIS real)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

REDIS_URL = "redis://localhost:6379/15"
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

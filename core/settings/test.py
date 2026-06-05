"""Settings para pytest."""
from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-secret-key"

from core.settings.apps_registry import build_installed_apps

# Apps que requieren GDAL/PostGIS — se excluyen del suite por defecto
# analytics importa Store (PostGIS); sin GDAL en el runner de pytest
GIS_DEPENDENT_MODULES = frozenset(
    {"stores", "products", "orders", "delivery", "analytics"}
)


def _exclude_from_test_apps(entry: str) -> bool:
    if entry in {"django.contrib.gis", "core.apps.CoreConfig"}:
        return True
    if entry.startswith("features.") and ".apps." in entry:
        return entry.split(".")[1] in GIS_DEPENDENT_MODULES
    return False


INSTALLED_APPS = [
    app
    for app in build_installed_apps(BASE_DIR)  # noqa: F405
    if not _exclude_from_test_apps(app)
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

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

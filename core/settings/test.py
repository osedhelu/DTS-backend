"""Settings para pytest."""
import os

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-secret-key"

from core.settings.apps_registry import build_installed_apps

# Apps que requieren GDAL/PostGIS — se excluyen del suite local sin GDAL
GIS_DEPENDENT_MODULES = frozenset(
    {"stores", "products", "orders", "delivery", "analytics", "marketing"}
)


def _exclude_from_test_apps(entry: str) -> bool:
    if entry in {"django.contrib.gis", "core.apps.CoreConfig"}:
        return True
    if entry.startswith("features.") and ".apps." in entry:
        return entry.split(".")[1] in GIS_DEPENDENT_MODULES
    return False


# GitHub Actions instala libgdal-dev y exporta GDAL_LIBRARY_PATH antes de pytest
_ci_postgis = os.environ.get("CI") == "true" and bool(
    os.environ.get("GDAL_LIBRARY_PATH")
)

if _ci_postgis:
    INSTALLED_APPS = build_installed_apps(BASE_DIR)  # noqa: F405
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": os.environ.get("POSTGRES_DB", "test_dts"),
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "TEST": {"NAME": "test_dts_django"},
        }
    }
else:
    INSTALLED_APPS = [
        app
        for app in build_installed_apps(BASE_DIR)  # noqa: F405
        if not _exclude_from_test_apps(app)
    ]
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

MEDIA_ROOT = BASE_DIR / "test_media"  # noqa: F405

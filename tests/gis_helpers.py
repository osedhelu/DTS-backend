"""Helpers compartidos para tests que requieren GDAL/PostGIS."""

from __future__ import annotations

import os
from pathlib import Path


def gdal_available() -> bool:
    try:
        from django.contrib.gis.gdal import GDAL_VERSION  # noqa: F401

        return True
    except Exception:
        return False


def postgis_tests_available() -> bool:
    try:
        from django.contrib.gis.gdal import GDAL_VERSION  # noqa: F401
        from django.contrib.gis.geos import Point

        Point(0, 0, srid=4326)
        return True
    except Exception:
        return False


def ci_postgis_enabled() -> bool:
    return os.environ.get("CI") == "true" and gdal_available()


def create_test_store(owner, *, name: str = "Tienda Test", status=None):
    """Crea Store con location PostGIS obligatoria."""
    from features.stores.domain.entities import StoreStatus
    from features.stores.domain.value_objects import GeoLocation
    from features.stores.infrastructure.models import Store

    if status is None:
        status = StoreStatus.OPEN
    status_value = status.value if hasattr(status, "value") else status

    store = Store(name=name, owner=owner, status=status_value)
    store.set_location(GeoLocation(latitude=4.711, longitude=-74.072))
    store.save()
    return store


BACKEND_DIR = Path(__file__).resolve().parents[1]

POSTGIS_DATABASE = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "test_dts",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_dts_django"},
    }
}

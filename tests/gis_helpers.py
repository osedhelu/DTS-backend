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

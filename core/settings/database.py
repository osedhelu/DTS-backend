"""Configuración de base de datos PostGIS — T1.1.2."""
from pathlib import Path


def build_databases(env, base_dir: Path) -> dict:
    return {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": env("DB_NAME", default="dts_delivery"),
            "USER": env("DB_USER", default="postgres"),
            "PASSWORD": env("DB_PASSWORD", default="postgres"),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="5432"),
            "OPTIONS": {
                "connect_timeout": env.int("DB_CONNECT_TIMEOUT", default=10),
            },
        }
    }

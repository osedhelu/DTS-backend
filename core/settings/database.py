"""Configuración de base de datos PostGIS — T1.1.2."""
from pathlib import Path

POSTGIS_ENGINE = "django.contrib.gis.db.backends.postgis"


def build_databases(env, base_dir: Path) -> dict:
    database_url = env("DATABASE_URL", default="")
    if str(database_url).strip():
        config = env.db("DATABASE_URL")
        config["ENGINE"] = POSTGIS_ENGINE
        config.setdefault("OPTIONS", {})
        config["OPTIONS"].setdefault(
            "connect_timeout", env.int("DB_CONNECT_TIMEOUT", default=10)
        )
        return {"default": config}

    return {
        "default": {
            "ENGINE": POSTGIS_ENGINE,
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

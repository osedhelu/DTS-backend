from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.db import connection

from core.settings.database import build_databases
from core.settings.redis_config import build_redis_url


class _FakeEnv:
    def __init__(self, values: dict | None = None):
        self._values = values or {}

    def __call__(self, key, default=None):
        return self._values.get(key, default)

    def int(self, key, default=0):
        return int(self._values.get(key, default))


def test_build_databases_uses_postgis_engine():
    config = build_databases(_FakeEnv(), base_dir="/tmp")
    assert config["default"]["ENGINE"] == "django.contrib.gis.db.backends.postgis"
    assert config["default"]["NAME"] == "dts_delivery"
    assert config["default"]["HOST"] == "localhost"
    assert config["default"]["PORT"] == "5432"


def test_build_databases_reads_env_overrides():
    env = _FakeEnv(
        {
            "DB_NAME": "custom_db",
            "DB_USER": "admin",
            "DB_PASSWORD": "secret",
            "DB_HOST": "db.internal",
            "DB_PORT": "5433",
            "DB_CONNECT_TIMEOUT": "30",
        }
    )
    config = build_databases(env, base_dir="/tmp")
    db = config["default"]
    assert db["NAME"] == "custom_db"
    assert db["USER"] == "admin"
    assert db["PASSWORD"] == "secret"
    assert db["HOST"] == "db.internal"
    assert db["PORT"] == "5433"
    assert db["OPTIONS"]["connect_timeout"] == 30


def test_build_redis_url_default():
    assert build_redis_url(_FakeEnv()) == "redis://localhost:6379/0"


def test_build_redis_url_from_env():
    env = _FakeEnv({"REDIS_URL": "redis://redis:6379/1"})
    assert build_redis_url(env) == "redis://redis:6379/1"


def test_redis_url_exposed_in_settings():
    assert settings.REDIS_URL.startswith("redis://")
    assert settings.CELERY_BROKER_URL == settings.REDIS_URL
    assert settings.CELERY_RESULT_BACKEND == settings.REDIS_URL


@pytest.mark.django_db
def test_database_connection_mock():
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    with patch.object(connection, "cursor", return_value=mock_cursor) as mock_conn:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        mock_conn.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT 1")

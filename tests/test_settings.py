import django
from django.conf import settings


def test_settings_load_without_error():
    assert settings.configured
    assert settings.SECRET_KEY
    assert "rest_framework" in settings.INSTALLED_APPS
    assert "drf_spectacular" in settings.INSTALLED_APPS


def test_test_settings_module_active():
    assert settings.SECRET_KEY == "test-secret-key"
    assert settings.DEBUG is False


def test_django_apps_ready():
    assert django.apps.apps.ready

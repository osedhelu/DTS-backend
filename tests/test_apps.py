import importlib

import pytest
from django.apps import apps as django_apps
from django.conf import settings

from core.settings.apps_registry import build_installed_apps, discover_django_apps


EXPECTED_FEATURES = [
    "features.accounts",
    "features.stores",
    "features.products",
    "features.orders",
    "features.delivery",
    "features.notifications",
    "features.analytics",
    "features.marketing",
]

def test_discover_django_apps_finds_all_features(settings):
    base_dir = settings.BASE_DIR
    discovered = discover_django_apps(base_dir)
    for app in EXPECTED_FEATURES:
        assert app in discovered


def test_build_installed_apps_includes_core_and_discovered(settings):
    installed = build_installed_apps(settings.BASE_DIR)
    assert "django.contrib.gis" in installed
    assert "rest_framework" in installed
    for app in EXPECTED_FEATURES:
        assert app in installed


@pytest.mark.parametrize("app_name", EXPECTED_FEATURES)
def test_each_app_is_importable(app_name):
    module = importlib.import_module(f"{app_name}.apps")
    assert module is not None


def test_all_registered_apps_are_loaded(settings):
    loaded_names = {config.name for config in django_apps.get_app_configs()}
    for app_name in settings.INSTALLED_APPS:
        assert app_name in loaded_names

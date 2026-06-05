import importlib

import pytest
from django.apps import apps as django_apps
from django.conf import settings

from core.settings.apps_registry import build_installed_apps, discover_django_apps


EXPECTED_FEATURES = [
    "features.accounts.apps.AccountsConfig",
    "features.stores.apps.StoresConfig",
    "features.products.apps.ProductsConfig",
    "features.orders.apps.OrdersConfig",
    "features.delivery.apps.DeliveryConfig",
    "features.notifications.apps.NotificationsConfig",
    "features.analytics.apps.AnalyticsConfig",
    "features.marketing.apps.MarketingConfig",
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


@pytest.mark.parametrize("app_config_path", EXPECTED_FEATURES)
def test_each_app_config_is_importable(app_config_path):
    module_path, class_name = app_config_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    assert getattr(module, class_name) is not None


def test_all_registered_apps_are_loaded(settings):
    loaded_labels = {config.label for config in django_apps.get_app_configs()}
    loaded_names = {config.name for config in django_apps.get_app_configs()}

    for entry in settings.INSTALLED_APPS:
        if entry.endswith("Config"):
            module_path, class_name = entry.rsplit(".", 1)
            config_class = getattr(importlib.import_module(module_path), class_name)
            assert config_class.label in loaded_labels
        else:
            assert entry in loaded_names


def test_core_config_is_last_app(settings):
    installed = build_installed_apps(settings.BASE_DIR)
    assert installed[-1] == "core.apps.CoreConfig"

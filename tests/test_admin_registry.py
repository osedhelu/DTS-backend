import pytest
from django.contrib import admin

from features.accounts.infrastructure.models import CustomUser, DeviceToken


@pytest.mark.django_db
def test_admin_registers_project_models():
    import features.accounts.infrastructure.admin  # noqa: F401

    assert CustomUser in admin.site._registry
    assert DeviceToken in admin.site._registry

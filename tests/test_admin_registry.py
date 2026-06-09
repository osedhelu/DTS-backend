import pytest
from django.contrib import admin

from features.accounts.infrastructure.models import CustomUser, DeviceToken


@pytest.mark.django_db
def test_admin_registers_project_models():
    import features.accounts.infrastructure.admin  # noqa: F401
    import features.products.infrastructure.admin  # noqa: F401
    import features.stores.infrastructure.admin  # noqa: F401
    from features.products.infrastructure.models import Product, ProductImage
    from features.stores.infrastructure.models import Store

    assert CustomUser in admin.site._registry
    assert DeviceToken in admin.site._registry
    assert Product in admin.site._registry
    assert ProductImage in admin.site._registry
    assert Store in admin.site._registry


def test_admin_image_preview_renders_img_tag():
    from core.admin_media import admin_image_preview

    html = admin_image_preview("/media/products/1/photo.png", alt="Producto")
    assert "<img" in html
    assert "/media/products/1/photo.png" in html
    assert 'alt="Producto"' in html


def test_admin_image_preview_empty_url():
    from core.admin_media import admin_image_preview

    assert admin_image_preview("") == "—"
    assert admin_image_preview(None) == "—"

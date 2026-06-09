from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings
from PIL import Image
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.products.domain.entities import ProductType
from tests.gis_helpers import POSTGIS_DATABASE, create_test_store, postgis_tests_available

BACKEND_DIR = Path(__file__).resolve().parents[4]


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


def _make_image(name: str = "burger.png") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_product_image_model():
    from features.products.infrastructure.models import Product, ProductImage

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        MEDIA_ROOT=BACKEND_DIR / "test_media_models",
    ):
        merchant = CustomUser.objects.create_user(
            username="merchant_image_model",
            email="image_model@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = create_test_store(merchant)
        product = Product.objects.create(
            store=store,
            name="Pizza margarita",
            price=Decimal("29900.00"),
            stock=5,
            product_type=ProductType.PHYSICAL,
        )

        image = ProductImage.objects.create(
            product=product,
            image=_make_image(),
            is_primary=True,
        )

        saved = ProductImage.objects.select_related("product").get(pk=image.pk)
        assert saved.product_id == product.pk
        assert saved.is_primary is True
        assert saved.image.name.startswith(f"products/{product.pk}/")


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_product_image_upload_api(api_client):
    from features.products.infrastructure.models import Product, ProductImage

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        MEDIA_ROOT=BACKEND_DIR / "test_media_api",
    ):
        merchant = CustomUser.objects.create_user(
            username="merchant_image_api",
            email="image_api@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = create_test_store(merchant)
        product = Product.objects.create(
            store=store,
            name="Tacos al pastor",
            price=Decimal("12000.00"),
            stock=20,
            product_type=ProductType.PHYSICAL,
        )
        _auth(api_client, merchant)

        response = api_client.post(
            f"/api/v1/stores/{store.pk}/products/{product.pk}/images/",
            {"image": _make_image("tacos.png"), "is_primary": True},
            format="multipart",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_primary"] is True
        assert "url" in response.data
        assert ProductImage.objects.filter(product=product).count() == 1


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_product_image_delete_and_set_primary_api(api_client):
    from features.products.infrastructure.models import Product, ProductImage

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        MEDIA_ROOT=BACKEND_DIR / "test_media_api_detail",
    ):
        merchant = CustomUser.objects.create_user(
            username="merchant_image_detail",
            email="image_detail@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = create_test_store(merchant)
        product = Product.objects.create(
            store=store,
            name="Hamburguesa",
            price=Decimal("15000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )
        primary = ProductImage.objects.create(
            product=product,
            image=_make_image("primary.png"),
            is_primary=True,
        )
        secondary = ProductImage.objects.create(
            product=product,
            image=_make_image("secondary.png"),
            is_primary=False,
        )
        _auth(api_client, merchant)

        patch_response = api_client.patch(
            f"/api/v1/stores/{store.pk}/products/{product.pk}/images/{secondary.pk}/",
            {"is_primary": True},
            format="multipart",
        )
        assert patch_response.status_code == status.HTTP_200_OK
        assert patch_response.data["is_primary"] is True

        primary.refresh_from_db()
        secondary.refresh_from_db()
        assert primary.is_primary is False
        assert secondary.is_primary is True

        delete_response = api_client.delete(
            f"/api/v1/stores/{store.pk}/products/{product.pk}/images/{secondary.pk}/",
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        assert ProductImage.objects.filter(product=product).count() == 1
        assert ProductImage.objects.get(pk=primary.pk).is_primary is True


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_list_products_includes_primary_image_url(api_client):
    from features.products.infrastructure.models import Product, ProductImage

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        MEDIA_ROOT=BACKEND_DIR / "test_media_list_primary",
    ):
        merchant = CustomUser.objects.create_user(
            username="merchant_list_primary",
            email="list_primary@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = create_test_store(merchant)
        product = Product.objects.create(
            store=store,
            name="Ensalada César",
            price=Decimal("8900.00"),
            stock=8,
            product_type=ProductType.PHYSICAL,
        )
        ProductImage.objects.create(
            product=product,
            image=_make_image("cesar.png"),
            is_primary=True,
        )

        response = api_client.get(f"/api/v1/stores/{store.pk}/products/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["primary_image_url"]
        assert f"/media/products/{product.pk}/" in response.data["results"][0]["primary_image_url"]

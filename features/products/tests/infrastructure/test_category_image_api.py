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
from features.products.infrastructure.models import Category, CategoryImage
from tests.gis_helpers import POSTGIS_DATABASE, create_test_store, postgis_tests_available

BACKEND_DIR = Path(__file__).resolve().parents[4]


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


def _make_image(name: str = "category.png") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color="blue").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_category_image_upload_and_primary_api(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        MEDIA_ROOT=BACKEND_DIR / "test_media_category_image",
    ):
        merchant = CustomUser.objects.create_user(
            username="merchant_category_image",
            email="category_image@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = create_test_store(merchant)
        category = Category.objects.create(store=store, name="Comida")
        subcategory = Category.objects.create(store=store, name="Hamburguesas", parent=category)
        _auth(api_client, merchant)

        upload_response = api_client.post(
            f"/api/v1/stores/{store.pk}/categories/{category.pk}/images/",
            {"image": _make_image("comida.png"), "is_primary": True},
            format="multipart",
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        assert upload_response.data["is_primary"] is True

        sub_upload = api_client.post(
            f"/api/v1/stores/{store.pk}/categories/{subcategory.pk}/images/",
            {"image": _make_image("burger.png"), "is_primary": True},
            format="multipart",
        )
        assert sub_upload.status_code == status.HTTP_201_CREATED

        tree_response = api_client.get(f"/api/v1/stores/{store.pk}/categories/")
        assert tree_response.status_code == status.HTTP_200_OK
        assert tree_response.data[0]["primary_image_url"]
        assert tree_response.data[0]["subcategories"][0]["primary_image_url"]

        image_id = upload_response.data["id"]
        second = api_client.post(
            f"/api/v1/stores/{store.pk}/categories/{category.pk}/images/",
            {"image": _make_image("comida2.png"), "is_primary": False},
            format="multipart",
        )
        assert second.status_code == status.HTTP_201_CREATED

        patch_response = api_client.patch(
            f"/api/v1/stores/{store.pk}/categories/{category.pk}/images/{second.data['id']}/",
            {"is_primary": True},
            format="multipart",
        )
        assert patch_response.status_code == status.HTTP_200_OK
        assert patch_response.data["is_primary"] is True

        delete_response = api_client.delete(
            f"/api/v1/stores/{store.pk}/categories/{category.pk}/images/{image_id}/",
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        assert CategoryImage.objects.filter(category=category).count() == 1

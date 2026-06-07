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
from features.stores.domain.entities import StoreStatus, StoreVertical

BACKEND_DIR = Path(__file__).resolve().parents[4]

POSTGIS_DATABASE = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "dts_delivery",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_dts_store_profile"},
    }
}


def _geos_available() -> bool:
    try:
        from django.contrib.gis.geos import Point

        Point(0, 0, srid=4326)
        return True
    except Exception:
        return False


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


def _make_test_image(name: str = "logo.png") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_store_profile_fields():
    from features.stores.domain.value_objects import GeoLocation
    from features.stores.infrastructure.models import Store as StoreModel

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        MEDIA_ROOT=BACKEND_DIR / "test_media_store_profile_fields",
    ):
        owner = CustomUser.objects.create_user(
            username="merchant_profile_fields",
            email="profile_fields@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = StoreModel(
            owner=owner,
            name="Tienda Perfil",
            status=StoreStatus.OPEN,
            vertical=StoreVertical.FOOD,
            address="Calle 10",
            description="Comida casera y delivery",
            phone="+57 300 123 4567",
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.logo = _make_test_image()
        store.save()

        saved = StoreModel.objects.get(pk=store.pk)
        assert saved.description == "Comida casera y delivery"
        assert saved.phone == "+57 300 123 4567"
        assert saved.logo.name.startswith("stores/")


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_update_store_profile_api(api_client):
    from features.stores.domain.value_objects import GeoLocation
    from features.stores.infrastructure.models import Store as StoreModel

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        MEDIA_ROOT=BACKEND_DIR / "test_media_store_profile_api",
    ):
        merchant = CustomUser.objects.create_user(
            username="merchant_profile_api",
            email="profile_api@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = StoreModel(
            owner=merchant,
            name="Nombre Original",
            status=StoreStatus.CLOSED,
            vertical=StoreVertical.SERVICES,
            description="Descripción inicial",
            phone="111",
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        _auth(api_client, merchant)

        get_response = api_client.get(f"/api/v1/stores/{store.id}/profile/")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data["name"] == "Nombre Original"
        assert get_response.data["vertical"] == StoreVertical.SERVICES
        assert get_response.data["description"] == "Descripción inicial"

        patch_response = api_client.patch(
            f"/api/v1/stores/{store.id}/profile/",
            {
                "name": "Tienda Actualizada",
                "description": "Nueva descripción del negocio",
                "phone": "+57 310 000 1111",
                "status": StoreStatus.OPEN,
                "logo": _make_test_image(),
            },
            format="multipart",
        )

        assert patch_response.status_code == status.HTTP_200_OK
        assert patch_response.data["name"] == "Tienda Actualizada"
        assert patch_response.data["description"] == "Nueva descripción del negocio"
        assert patch_response.data["phone"] == "+57 310 000 1111"
        assert patch_response.data["status"] == StoreStatus.OPEN
        assert patch_response.data["is_open"] is True
        assert patch_response.data["logo_url"]

        store.refresh_from_db()
        assert store.name == "Tienda Actualizada"
        assert store.description == "Nueva descripción del negocio"
        assert store.phone == "+57 310 000 1111"
        assert store.status == StoreStatus.OPEN
        assert store.logo.name.startswith("stores/")

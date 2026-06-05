from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.stores.domain.entities import StoreStatus

BACKEND_DIR = Path(__file__).resolve().parents[4]

POSTGIS_DATABASE = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "dts_delivery",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_dts_stores_api"},
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


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_list_stores_public(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.stores.domain.value_objects import GeoLocation
        from features.stores.infrastructure.models import Store as StoreModel

        merchant = CustomUser.objects.create_user(
            username="merchant_list",
            email="merchant_list@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = StoreModel(owner=merchant, name="Tienda Pública", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        response = api_client.get("/api/v1/stores/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Tienda Pública"
        assert response.data["results"][0]["is_open"] is True


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_merchant_update_own_store(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.stores.domain.value_objects import GeoLocation
        from features.stores.infrastructure.models import Store as StoreModel

        merchant = CustomUser.objects.create_user(
            username="merchant_update",
            email="merchant_update@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = StoreModel(owner=merchant, name="Mi Tienda", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        _auth(api_client, merchant)
        response = api_client.patch(
            f"/api/v1/stores/{store.id}/",
            {"status": StoreStatus.CLOSED},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == StoreStatus.CLOSED
        assert response.data["is_open"] is False

        store.refresh_from_db()
        assert store.status == StoreStatus.CLOSED

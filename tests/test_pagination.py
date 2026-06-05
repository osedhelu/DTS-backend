from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from core.api.pagination import paginate_list
from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.stores.domain.entities import StoreStatus
from features.stores.domain.value_objects import GeoLocation

BACKEND_DIR = Path(__file__).resolve().parents[1]

POSTGIS_DATABASE = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "dts_delivery",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_dts_pagination"},
    }
}


def _geos_available() -> bool:
    try:
        from django.contrib.gis.geos import Point

        Point(0, 0, srid=4326)
        return True
    except Exception:
        return False


def test_pagination():
    factory = APIRequestFactory()
    request = Request(factory.get("/api/v1/stores/", {"page": "2", "page_size": "5"}))
    items = [{"id": index, "name": f"item-{index}"} for index in range(23)]

    response = paginate_list(request, items, lambda page: page)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 23
    assert len(response.data["results"]) == 5
    assert response.data["results"][0]["id"] == 5
    assert response.data["previous"] is not None
    assert response.data["next"] is not None


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_pagination_on_stores_api(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_pagination",
            email="merchant_pagination@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )

        for index in range(7):
            store = Store(
                owner=merchant,
                name=f"Tienda {index}",
                status=StoreStatus.OPEN if index % 2 == 0 else StoreStatus.CLOSED,
            )
            store.set_location(GeoLocation(latitude=4.71 + index * 0.001, longitude=-74.07))
            store.save()

        page_one = api_client.get("/api/v1/stores/", {"page": 1, "page_size": 3})
        assert page_one.status_code == status.HTTP_200_OK
        assert page_one.data["count"] == 7
        assert len(page_one.data["results"]) == 3
        assert page_one.data["next"] is not None

        filtered = api_client.get("/api/v1/stores/", {"status": StoreStatus.OPEN.value})
        assert filtered.status_code == status.HTTP_200_OK
        assert filtered.data["count"] == 4
        assert all(item["status"] == StoreStatus.OPEN for item in filtered.data["results"])

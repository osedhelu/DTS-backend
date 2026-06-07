import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from tests.gis_helpers import postgis_tests_available


@pytest.fixture
def merchant_user(db):
    return CustomUser.objects.create_user(
        username="merchant",
        email="merchant@example.com",
        password="pass123",
        role=UserRole.MERCHANT.value,
    )


@pytest.fixture
def other_merchant(db):
    return CustomUser.objects.create_user(
        username="other",
        email="other@example.com",
        password="pass123",
        role=UserRole.MERCHANT.value,
    )


@pytest.fixture
def merchant_store(db, merchant_user):
    from features.stores.domain.entities import StoreStatus
    from features.stores.domain.value_objects import GeoLocation
    from features.stores.infrastructure.models import Store

    store = Store(
        name="Mi Tienda",
        owner=merchant_user,
        status=StoreStatus.OPEN.value,
    )
    store.set_location(GeoLocation(latitude=4.711, longitude=-74.072))
    store.save()
    return store


@pytest.fixture
def other_store(db, other_merchant):
    from features.stores.domain.entities import StoreStatus
    from features.stores.domain.value_objects import GeoLocation
    from features.stores.infrastructure.models import Store

    store = Store(
        name="Otra Tienda",
        owner=other_merchant,
        status=StoreStatus.OPEN.value,
    )
    store.set_location(GeoLocation(latitude=4.712, longitude=-74.073))
    store.save()
    return store


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido. CI instala libgdal-dev; local: brew install gdal geos",
)
@pytest.mark.django_db
def test_merchant_list_own_stores(merchant_user, merchant_store, other_store):
    client = APIClient()
    client.force_authenticate(user=merchant_user)

    response = client.get(reverse("stores-mine"))
    assert response.status_code == status.HTTP_200_OK

    payload = response.json()
    results = payload["results"] if "results" in payload else payload
    assert len(results) == 1
    assert results[0]["id"] == merchant_store.id
    assert results[0]["name"] == "Mi Tienda"


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido. CI instala libgdal-dev; local: brew install gdal geos",
)
@pytest.mark.django_db
def test_merchant_list_own_stores_includes_suspended(merchant_user, merchant_store):
    merchant_store.is_active = False
    merchant_store.save(update_fields=["is_active"])

    client = APIClient()
    client.force_authenticate(user=merchant_user)

    response = client.get(reverse("stores-mine"))
    assert response.status_code == status.HTTP_200_OK

    payload = response.json()
    results = payload["results"] if "results" in payload else payload
    assert len(results) == 1
    assert results[0]["id"] == merchant_store.id

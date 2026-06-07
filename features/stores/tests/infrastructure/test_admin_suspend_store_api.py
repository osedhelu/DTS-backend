import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from tests.gis_helpers import postgis_tests_available


@pytest.fixture
def super_admin(db):
    return CustomUser.objects.create_user(
        username="superadmin",
        email="super@example.com",
        password="pass123",
        role=UserRole.SUPER_ADMIN.value,
    )


@pytest.fixture
def merchant_user(db):
    return CustomUser.objects.create_user(
        username="merchant",
        email="merchant@example.com",
        password="pass123",
        role=UserRole.MERCHANT.value,
    )


@pytest.fixture
def store(db, merchant_user):
    from features.stores.domain.entities import StoreStatus
    from features.stores.domain.value_objects import GeoLocation
    from features.stores.infrastructure.models import Store

    store = Store(
        name="Tienda Test",
        owner=merchant_user,
        status=StoreStatus.OPEN.value,
        is_active=True,
    )
    store.set_location(GeoLocation(latitude=4.711, longitude=-74.072))
    store.save()
    return store


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido. CI instala libgdal-dev; local: brew install gdal geos",
)
@pytest.mark.django_db
def test_admin_suspend_store_api(super_admin, store):
    client = APIClient()
    client.force_authenticate(user=super_admin)

    response = client.patch(
        reverse("stores-admin-moderation", kwargs={"store_id": store.id}),
        {"is_active": False},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_active"] is False

    store.refresh_from_db()
    assert store.is_active is False


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido. CI instala libgdal-dev; local: brew install gdal geos",
)
@pytest.mark.django_db
def test_admin_reactivate_store_api(super_admin, store):
    store.is_active = False
    store.save(update_fields=["is_active"])

    client = APIClient()
    client.force_authenticate(user=super_admin)

    response = client.patch(
        reverse("stores-admin-moderation", kwargs={"store_id": store.id}),
        {"is_active": True},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_active"] is True


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido. CI instala libgdal-dev; local: brew install gdal geos",
)
@pytest.mark.django_db
def test_suspended_store_hidden_from_public_list(api_client, store):
    store.is_active = False
    store.save(update_fields=["is_active"])

    response = api_client.get(reverse("stores-list-create"))
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    results = payload["results"] if "results" in payload else payload
    store_ids = [item["id"] for item in results]
    assert store.id not in store_ids


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido. CI instala libgdal-dev; local: brew install gdal geos",
)
@pytest.mark.django_db
def test_admin_suspend_store_forbidden_for_merchant(merchant_user, store):
    client = APIClient()
    client.force_authenticate(user=merchant_user)

    response = client.patch(
        reverse("stores-admin-moderation", kwargs={"store_id": store.id}),
        {"is_active": False},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

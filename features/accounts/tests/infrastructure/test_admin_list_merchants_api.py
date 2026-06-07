import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, MerchantProfile
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
        email_verified=False,
        is_active=False,
    )


@pytest.fixture
def verified_merchant(db):
    user = CustomUser.objects.create_user(
        username="verified",
        email="verified@example.com",
        password="pass123",
        role=UserRole.MERCHANT.value,
        email_verified=True,
        is_active=True,
    )
    MerchantProfile.objects.create(
        user=user,
        business_name="Comercio Verificado",
        phone="+573001112233",
    )
    return user


@pytest.fixture
def store(db, merchant_user):
    from features.stores.domain.entities import StoreStatus
    from features.stores.domain.value_objects import GeoLocation
    from features.stores.infrastructure.models import Store

    MerchantProfile.objects.create(
        user=merchant_user,
        business_name="Tacos Ana",
        phone="+573009998877",
    )
    store = Store(
        name="Tacos Ana",
        owner=merchant_user,
        status=StoreStatus.CLOSED.value,
    )
    store.set_location(GeoLocation(latitude=4.711, longitude=-74.072))
    store.save()
    return store


@pytest.fixture
def verified_store(db, verified_merchant):
    from features.stores.domain.entities import StoreStatus
    from features.stores.domain.value_objects import GeoLocation
    from features.stores.infrastructure.models import Store

    store = Store(
        name="Comercio Verificado",
        owner=verified_merchant,
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
def test_admin_list_merchants_api(super_admin, store, verified_store):
    client = APIClient()
    client.force_authenticate(user=super_admin)

    response = client.get(reverse("accounts-admin-merchants"))
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    results = payload["results"] if "results" in payload else payload
    assert len(results) == 2

    pending = next(item for item in results if item["email"] == "merchant@example.com")
    assert pending["email_verified"] is False
    assert pending["user_is_active"] is False
    assert pending["business_name"] == "Tacos Ana"
    assert pending["store_name"] == "Tacos Ana"

    verified = next(item for item in results if item["email"] == "verified@example.com")
    assert verified["email_verified"] is True
    assert verified["user_is_active"] is True


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido. CI instala libgdal-dev; local: brew install gdal geos",
)
@pytest.mark.django_db
def test_admin_list_merchants_filters_by_email_verified(super_admin, store, verified_store):
    client = APIClient()
    client.force_authenticate(user=super_admin)

    response = client.get(reverse("accounts-admin-merchants"), {"email_verified": "false"})
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    results = payload["results"] if "results" in payload else payload
    assert len(results) == 1
    assert results[0]["email"] == "merchant@example.com"


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido. CI instala libgdal-dev; local: brew install gdal geos",
)
@pytest.mark.django_db
def test_admin_list_merchants_forbidden_for_merchant(merchant_user, store):
    client = APIClient()
    client.force_authenticate(user=merchant_user)

    response = client.get(reverse("accounts-admin-merchants"))
    assert response.status_code == status.HTTP_403_FORBIDDEN

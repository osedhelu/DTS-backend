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
    )
    store.set_location(GeoLocation(latitude=4.711, longitude=-74.072))
    store.save()
    return store


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido. CI instala libgdal-dev; local: brew install gdal geos",
)
@pytest.mark.django_db
def test_admin_metrics_returns_sales_active_stores_and_delivery_time(
    super_admin, store, merchant_user
):
    from features.analytics.infrastructure.models import DailySalesReport
    from features.orders.domain.value_objects import OrderStatus, OrderType
    from features.orders.infrastructure.models import Order

    DailySalesReport.objects.create(
        report_date="2026-06-01",
        store=store,
        order_count=2,
        gross_revenue="150000.00",
    )

    Order.objects.create(
        customer=merchant_user,
        store=store,
        status=OrderStatus.DELIVERED.value,
        order_type=OrderType.DELIVERY.value,
        total="50000.00",
    )

    client = APIClient()
    client.force_authenticate(user=super_admin)
    response = client.get(reverse("analytics-admin-metrics"))

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["active_stores"] == 1
    assert len(payload["sales_series"]) == 7
    assert any(point["total"] != "0" for point in payload["sales_series"])


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido. CI instala libgdal-dev; local: brew install gdal geos",
)
@pytest.mark.django_db
def test_admin_metrics_forbidden_for_merchant(merchant_user):
    client = APIClient()
    client.force_authenticate(user=merchant_user)
    response = client.get(reverse("analytics-admin-metrics"))

    assert response.status_code == status.HTTP_403_FORBIDDEN

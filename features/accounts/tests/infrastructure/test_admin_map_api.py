import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.delivery.infrastructure.models import DeliveryTracking, TrackingPoint
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.orders.infrastructure.models import Order
from features.stores.domain.value_objects import GeoLocation
from features.stores.infrastructure.models import Store
from tests.gis_helpers import postgis_tests_available


@pytest.fixture
def super_admin(db):
    return CustomUser.objects.create_user(
        username="superadmin_map",
        email="super_map@example.com",
        password="pass123",
        role=UserRole.SUPER_ADMIN.value,
    )


@pytest.fixture
def merchant_user(db):
    return CustomUser.objects.create_user(
        username="merchant_map",
        email="merchant_map@example.com",
        password="pass123",
        role=UserRole.MERCHANT.value,
    )


@pytest.fixture
def map_store(db, merchant_user):
    store = Store(name="Pizza Norte", owner=merchant_user, address="Calle 100")
    store.set_location(GeoLocation(latitude=4.711, longitude=-74.072))
    store.save()
    return store


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido",
)
@pytest.mark.django_db
def test_admin_operations_map_api(api_client, super_admin, map_store):
    customer = CustomUser.objects.create_user(
        username="customer_map",
        email="customer_map@example.com",
        password="pass123",
        role=UserRole.CUSTOMER.value,
    )

    order = Order.objects.create(
        customer=customer,
        store=map_store,
        status=OrderStatus.ON_THE_WAY.value,
        order_type=OrderType.DELIVERY.value,
        total="25000.00",
    )
    tracking = DeliveryTracking.objects.create(order=order)
    point = TrackingPoint(
        tracking=tracking,
        sequence=1,
        recorded_at=timezone.now(),
    )
    point.set_location(GeoLocation(latitude=4.720, longitude=-74.080))
    point.save()

    api_client.force_authenticate(user=super_admin)
    response = api_client.get(reverse("accounts-admin-map"))

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert len(payload["stores"]) == 1
    assert payload["stores"][0]["name"] == "Pizza Norte"
    assert payload["stores"][0]["latitude"] == pytest.approx(4.711)
    assert len(payload["active_deliveries"]) == 1
    assert payload["active_deliveries"][0]["order_id"] == order.id
    assert payload["active_deliveries"][0]["latest_latitude"] == pytest.approx(4.720)


@pytest.mark.django_db
def test_admin_operations_map_forbidden_for_merchant(api_client, merchant_user):
    api_client.force_authenticate(user=merchant_user)
    response = api_client.get(reverse("accounts-admin-map"))
    assert response.status_code == status.HTTP_403_FORBIDDEN

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
def merchant_user(db):
    return CustomUser.objects.create_user(
        username="merchant_ops_map",
        email="merchant_ops_map@example.com",
        password="pass123",
        role=UserRole.MERCHANT.value,
    )


@pytest.fixture
def other_merchant(db):
    return CustomUser.objects.create_user(
        username="other_merchant_map",
        email="other_merchant_map@example.com",
        password="pass123",
        role=UserRole.MERCHANT.value,
    )


@pytest.fixture
def merchant_store(db, merchant_user):
    store = Store(name="Café Sur", owner=merchant_user, address="Calle 50")
    store.set_location(GeoLocation(latitude=4.65, longitude=-74.08))
    store.save()
    return store


@pytest.fixture
def other_store(db, other_merchant):
    store = Store(name="Otro Comercio", owner=other_merchant, address="Calle 80")
    store.set_location(GeoLocation(latitude=4.70, longitude=-74.05))
    store.save()
    return store


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido",
)
@pytest.mark.django_db
def test_merchant_operations_map_returns_own_stores_and_deliveries(
    api_client, merchant_user, merchant_store, other_store
):
    customer = CustomUser.objects.create_user(
        username="customer_merchant_map",
        email="customer_merchant_map@example.com",
        password="pass123",
        role=UserRole.CUSTOMER.value,
    )

    order = Order.objects.create(
        customer=customer,
        store=merchant_store,
        status=OrderStatus.ON_THE_WAY.value,
        order_type=OrderType.DELIVERY.value,
        total="18000.00",
        service_address="Calle 60",
        service_latitude=4.66,
        service_longitude=-74.09,
    )

    tracking = DeliveryTracking.objects.create(order=order)
    point = TrackingPoint(
        tracking=tracking,
        sequence=1,
        recorded_at=timezone.now(),
    )
    point.set_location(GeoLocation(latitude=4.655, longitude=-74.085))
    point.save()

    api_client.force_authenticate(user=merchant_user)
    response = api_client.get(reverse("stores-mine-operations-map"))

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert len(payload["stores"]) == 1
    assert payload["stores"][0]["name"] == "Café Sur"
    assert len(payload["active_deliveries"]) == 1
    assert payload["active_deliveries"][0]["order_id"] == order.id
    assert payload["active_deliveries"][0]["latest_latitude"] == pytest.approx(4.655)


@pytest.mark.django_db
def test_merchant_operations_map_forbidden_for_customer(api_client):
    customer = CustomUser.objects.create_user(
        username="customer_only_map",
        email="customer_only_map@example.com",
        password="pass123",
        role=UserRole.CUSTOMER.value,
    )
    api_client.force_authenticate(user=customer)
    response = api_client.get(reverse("stores-mine-operations-map"))
    assert response.status_code == status.HTTP_403_FORBIDDEN

import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.models import Order
from features.stores.domain.entities import StoreStatus
from features.stores.domain.value_objects import GeoLocation
from features.stores.infrastructure.models import Store


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


@pytest.mark.django_db
def test_order_chat_messages_roundtrip(api_client):
    merchant = CustomUser.objects.create_user(
        username="m_chat",
        email="m_chat@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
    )
    customer = CustomUser.objects.create_user(
        username="c_chat",
        email="c_chat@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    driver = CustomUser.objects.create_user(
        username="d_chat",
        email="d_chat@test.com",
        password="securepass123",
        role=UserRole.DRIVER,
    )
    store = Store(owner=merchant, name="Chat Store", status=StoreStatus.OPEN)
    store.set_location(GeoLocation(latitude=4.71, longitude=-74.07))
    store.save()
    order = Order.objects.create(
        customer=customer,
        store=store,
        driver=driver,
        status=OrderStatus.ON_THE_WAY,
        total="10000.00",
    )

    _auth(api_client, driver)
    create = api_client.post(
        f"/api/v1/orders/{order.id}/messages/",
        {"body": "Voy llegando"},
        format="json",
    )
    assert create.status_code == status.HTTP_201_CREATED
    assert create.data["body"] == "Voy llegando"
    assert create.data["sender_role"] == UserRole.DRIVER

    _auth(api_client, customer)
    listing = api_client.get(f"/api/v1/orders/{order.id}/messages/")
    assert listing.status_code == status.HTTP_200_OK
    assert len(listing.data) == 1
    assert listing.data[0]["body"] == "Voy llegando"

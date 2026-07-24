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


@pytest.mark.django_db
def test_merchant_owner_can_list_and_post_messages(api_client):
    merchant = CustomUser.objects.create_user(
        username="m_owner_chat",
        email="m_owner_chat@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
    )
    stranger = CustomUser.objects.create_user(
        username="m_stranger_chat",
        email="m_stranger_chat@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
    )
    customer = CustomUser.objects.create_user(
        username="c_owner_chat",
        email="c_owner_chat@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    store = Store(owner=merchant, name="Owner Chat Store", status=StoreStatus.OPEN)
    store.set_location(GeoLocation(latitude=4.71, longitude=-74.07))
    store.save()
    order = Order.objects.create(
        customer=customer,
        store=store,
        status=OrderStatus.ACCEPTED_BY_MERCHANT,
        total="5000.00",
    )

    _auth(api_client, merchant)
    create = api_client.post(
        f"/api/v1/orders/{order.id}/messages/",
        {"body": "Tu pedido sale en 10 min"},
        format="json",
    )
    assert create.status_code == status.HTTP_201_CREATED
    assert create.data["sender_role"] == UserRole.MERCHANT

    listing = api_client.get(f"/api/v1/orders/{order.id}/messages/")
    assert listing.status_code == status.HTTP_200_OK
    assert len(listing.data) == 1

    _auth(api_client, stranger)
    denied = api_client.get(f"/api/v1/orders/{order.id}/messages/")
    assert denied.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_ws_message_path_does_not_duplicate_via_rest_broadcast(api_client, monkeypatch):
    """B9: un POST REST crea una sola fila; broadcast no inserta otra."""
    from features.chat.infrastructure.models import OrderChatMessage

    merchant = CustomUser.objects.create_user(
        username="m_nodup",
        email="m_nodup@test.com",
        password="x",
        role=UserRole.MERCHANT,
    )
    customer = CustomUser.objects.create_user(
        username="c_nodup",
        email="c_nodup@test.com",
        password="x",
        role=UserRole.CUSTOMER,
    )
    store = Store(owner=merchant, name="NoDup", status=StoreStatus.OPEN)
    store.set_location(GeoLocation(latitude=4.71, longitude=-74.07))
    store.save()
    order = Order.objects.create(
        customer=customer,
        store=store,
        status=OrderStatus.ACCEPTED_BY_MERCHANT,
        total="1000.00",
    )

    monkeypatch.setattr(
        "features.chat.application.use_cases.send_order_message._broadcast_chat_message",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "features.chat.application.use_cases.send_order_message._enqueue_chat_push",
        lambda *a, **k: None,
    )

    _auth(api_client, merchant)
    api_client.post(
        f"/api/v1/orders/{order.id}/messages/",
        {"body": "hola"},
        format="json",
    )
    assert OrderChatMessage.objects.filter(order_id=order.id).count() == 1

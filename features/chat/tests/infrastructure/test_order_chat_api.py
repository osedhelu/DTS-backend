import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.chat.infrastructure.models import ChatMessageType, OrderChatMessage
from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.models import Order
from features.stores.domain.entities import StoreStatus
from features.stores.domain.value_objects import GeoLocation
from features.stores.infrastructure.models import Store


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


def _jpeg_upload(name: str = "pod.jpg") -> SimpleUploadedFile:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color=(255, 0, 0)).save(buf, format="JPEG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


def _seed_chat_order(**status_kw):
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
        status=status_kw.get("status", OrderStatus.ON_THE_WAY),
        total="10000.00",
    )
    return merchant, customer, driver, order


@pytest.mark.django_db
def test_order_chat_messages_roundtrip(api_client):
    _, customer, driver, order = _seed_chat_order()

    _auth(api_client, driver)
    create = api_client.post(
        f"/api/v1/orders/{order.id}/messages/",
        {"body": "Voy llegando"},
        format="json",
    )
    assert create.status_code == status.HTTP_201_CREATED
    assert create.data["body"] == "Voy llegando"
    assert create.data["sender_role"] == UserRole.DRIVER
    assert create.data["message_type"] == ChatMessageType.TEXT

    _auth(api_client, customer)
    listing = api_client.get(f"/api/v1/orders/{order.id}/messages/")
    assert listing.status_code == status.HTTP_200_OK
    assert listing.data["chat_closed"] is False
    assert len(listing.data["messages"]) == 1
    assert listing.data["messages"][0]["body"] == "Voy llegando"


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
    assert listing.data["chat_closed"] is False
    assert len(listing.data["messages"]) == 1

    _auth(api_client, stranger)
    denied = api_client.get(f"/api/v1/orders/{order.id}/messages/")
    assert denied.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_ws_message_path_does_not_duplicate_via_rest_broadcast(api_client, monkeypatch):
    """B9: un POST REST crea una sola fila; broadcast no inserta otra."""
    _, _, driver, order = _seed_chat_order()

    _auth(api_client, driver)
    create = api_client.post(
        f"/api/v1/orders/{order.id}/messages/",
        {"body": "solo uno"},
        format="json",
    )
    assert create.status_code == status.HTTP_201_CREATED
    assert OrderChatMessage.objects.filter(order_id=order.id).count() == 1


@pytest.mark.django_db
def test_chat_closed_after_delivered_rejects_post(api_client):
    _, customer, driver, order = _seed_chat_order(status=OrderStatus.DELIVERED)

    _auth(api_client, customer)
    listing = api_client.get(f"/api/v1/orders/{order.id}/messages/")
    assert listing.status_code == status.HTTP_200_OK
    assert listing.data["chat_closed"] is True

    denied = api_client.post(
        f"/api/v1/orders/{order.id}/messages/",
        {"body": "hola"},
        format="json",
    )
    assert denied.status_code == status.HTTP_403_FORBIDDEN

    _auth(api_client, driver)
    denied_driver = api_client.post(
        f"/api/v1/orders/{order.id}/messages/",
        {"body": "hola"},
        format="json",
    )
    assert denied_driver.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_proof_of_delivery_posts_image_message_and_closes_chat(api_client):
    _, customer, driver, order = _seed_chat_order()
    photo = _jpeg_upload()

    _auth(api_client, driver)
    pod = api_client.post(
        f"/api/v1/orders/{order.id}/proof-of-delivery/",
        {"photo": photo},
        format="multipart",
    )
    assert pod.status_code == status.HTTP_201_CREATED
    assert pod.data["chat_closed"] is True
    assert pod.data["photo_url"]

    order.refresh_from_db()
    assert order.status == OrderStatus.DELIVERED

    msg = OrderChatMessage.objects.filter(order_id=order.id).get()
    assert msg.message_type == ChatMessageType.IMAGE
    assert msg.body == "Pedido entregado"
    assert msg.image.name

    _auth(api_client, customer)
    listing = api_client.get(f"/api/v1/orders/{order.id}/messages/")
    assert listing.data["chat_closed"] is True
    assert len(listing.data["messages"]) == 1
    assert listing.data["messages"][0]["message_type"] == "image"
    assert listing.data["messages"][0]["image_url"]

    blocked = api_client.post(
        f"/api/v1/orders/{order.id}/messages/",
        {"body": "gracias"},
        format="json",
    )
    assert blocked.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_proof_of_delivery_requires_photo(api_client):
    _, _, driver, order = _seed_chat_order()
    _auth(api_client, driver)
    res = api_client.post(
        f"/api/v1/orders/{order.id}/proof-of-delivery/",
        {"notes": "sin foto"},
        format="multipart",
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

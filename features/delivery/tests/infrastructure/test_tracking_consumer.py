"""T5.1.2 — TrackingConsumer: connect + auth JWT."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.urls import path
from rest_framework_simplejwt.tokens import RefreshToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.delivery.infrastructure.consumers import (
    TrackingConsumer,
    TrackingOrderAccess,
)
from features.delivery.infrastructure.ws_auth import JwtAuthMiddlewareStack


def _ws_application():
    return JwtAuthMiddlewareStack(
        URLRouter(
            [
                path(
                    "ws/orders/<int:order_id>/tracking/",
                    TrackingConsumer.as_asgi(),
                ),
            ]
        )
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_consumer_connect_auth():
    customer = await database_sync_to_async(CustomUser.objects.create_user)(
        username="ws_tracking_customer",
        email="ws_tracking_customer@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    stranger = await database_sync_to_async(CustomUser.objects.create_user)(
        username="ws_tracking_stranger",
        email="ws_tracking_stranger@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    driver = await database_sync_to_async(CustomUser.objects.create_user)(
        username="ws_tracking_driver",
        email="ws_tracking_driver@test.com",
        password="securepass123",
        role=UserRole.DRIVER,
    )

    order_access = TrackingOrderAccess(
        order_id=42,
        customer_id=customer.id,
        driver_id=driver.id,
    )

    customer_token = str(
        await database_sync_to_async(lambda: RefreshToken.for_user(customer).access_token)()
    )
    stranger_token = str(
        await database_sync_to_async(lambda: RefreshToken.for_user(stranger).access_token)()
    )
    driver_token = str(
        await database_sync_to_async(lambda: RefreshToken.for_user(driver).access_token)()
    )

    application = _ws_application()

    with patch(
        "features.delivery.infrastructure.consumers.get_tracking_order_access",
        return_value=order_access,
    ):
        ok_comm = WebsocketCommunicator(
            application,
            f"/ws/orders/42/tracking/?token={customer_token}",
        )
        connected, _ = await ok_comm.connect()
        assert connected is True
        await ok_comm.disconnect()

        driver_comm = WebsocketCommunicator(
            application,
            f"/ws/orders/42/tracking/?token={driver_token}",
        )
        connected, _ = await driver_comm.connect()
        assert connected is True
        await driver_comm.disconnect()

        forbidden_comm = WebsocketCommunicator(
            application,
            f"/ws/orders/42/tracking/?token={stranger_token}",
        )
        connected, _ = await forbidden_comm.connect()
        assert connected is False
        await forbidden_comm.disconnect()

    no_token = WebsocketCommunicator(application, "/ws/orders/42/tracking/")
    connected, _ = await no_token.connect()
    assert connected is False
    await no_token.disconnect()

    with patch(
        "features.delivery.infrastructure.consumers.get_tracking_order_access",
        return_value=None,
    ):
        missing = WebsocketCommunicator(
            application,
            f"/ws/orders/99/tracking/?token={customer_token}",
        )
        connected, _ = await missing.connect()
        assert connected is False
        await missing.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_consumer_connect_auth_bearer_header():
    customer = await database_sync_to_async(CustomUser.objects.create_user)(
        username="ws_bearer_customer",
        email="ws_bearer_customer@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    token = str(
        await database_sync_to_async(lambda: RefreshToken.for_user(customer).access_token)()
    )
    order_access = TrackingOrderAccess(
        order_id=7,
        customer_id=customer.id,
        driver_id=None,
    )

    with patch(
        "features.delivery.infrastructure.consumers.get_tracking_order_access",
        return_value=order_access,
    ):
        communicator = WebsocketCommunicator(
            _ws_application(),
            "/ws/orders/7/tracking/",
            headers=[(b"authorization", f"Bearer {token}".encode())],
        )
        connected, _ = await communicator.connect()
        assert connected is True
        await communicator.disconnect()


def test_user_can_join_tracking_helpers():
    from features.delivery.infrastructure.consumers import user_can_join_tracking

    order = TrackingOrderAccess(order_id=1, customer_id=10, driver_id=20)
    assert user_can_join_tracking(SimpleNamespace(id=10, is_authenticated=True), order)
    assert user_can_join_tracking(SimpleNamespace(id=20, is_authenticated=True), order)
    assert not user_can_join_tracking(
        SimpleNamespace(id=99, is_authenticated=True), order
    )
    assert not user_can_join_tracking(
        SimpleNamespace(id=10, is_authenticated=False), order
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_location_broadcast_to_customer():
    """T5.2.1 — driver envía lat/lng; el customer del room recibe el broadcast."""
    customer = await database_sync_to_async(CustomUser.objects.create_user)(
        username="ws_broadcast_customer",
        email="ws_broadcast_customer@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    driver = await database_sync_to_async(CustomUser.objects.create_user)(
        username="ws_broadcast_driver",
        email="ws_broadcast_driver@test.com",
        password="securepass123",
        role=UserRole.DRIVER,
    )

    order_access = TrackingOrderAccess(
        order_id=100,
        customer_id=customer.id,
        driver_id=driver.id,
    )
    customer_token = str(
        await database_sync_to_async(
            lambda: RefreshToken.for_user(customer).access_token
        )()
    )
    driver_token = str(
        await database_sync_to_async(lambda: RefreshToken.for_user(driver).access_token)()
    )

    application = _ws_application()
    expected_payload = {
        "type": "location",
        "order_id": 100,
        "latitude": 4.7110,
        "longitude": -74.0721,
        "recorded_at": "2026-07-12T21:00:00+00:00",
        "sequence": 1,
    }

    with (
        patch(
            "features.delivery.infrastructure.consumers.get_tracking_order_access",
            return_value=order_access,
        ),
        patch(
            "features.delivery.infrastructure.consumers.record_driver_location_from_ws",
            return_value=expected_payload,
        ) as persist_mock,
    ):
        customer_ws = WebsocketCommunicator(
            application,
            f"/ws/orders/100/tracking/?token={customer_token}",
        )
        driver_ws = WebsocketCommunicator(
            application,
            f"/ws/orders/100/tracking/?token={driver_token}",
        )

        connected_c, _ = await customer_ws.connect()
        connected_d, _ = await driver_ws.connect()
        assert connected_c is True
        assert connected_d is True

        await driver_ws.send_json_to(
            {
                "type": "location",
                "latitude": 4.7110,
                "longitude": -74.0721,
            }
        )

        customer_msg = await customer_ws.receive_json_from()
        assert customer_msg == expected_payload

        # El conductor también está en el room y recibe el mismo evento.
        driver_msg = await driver_ws.receive_json_from()
        assert driver_msg == expected_payload

        persist_mock.assert_called_once()
        call_kwargs = persist_mock.call_args.kwargs
        assert call_kwargs["order_id"] == 100
        assert call_kwargs["driver_id"] == driver.id
        assert call_kwargs["latitude"] == 4.7110
        assert call_kwargs["longitude"] == -74.0721

        # Cliente no puede emitir ubicación.
        await customer_ws.send_json_to(
            {"type": "location", "latitude": 1.0, "longitude": 2.0}
        )
        error = await customer_ws.receive_json_from()
        assert error["type"] == "error"

        await customer_ws.disconnect()
        await driver_ws.disconnect()

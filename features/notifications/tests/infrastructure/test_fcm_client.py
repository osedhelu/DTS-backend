from unittest.mock import MagicMock, patch

import pytest

from features.notifications.domain.exceptions import FCMNotConfiguredError
from features.notifications.infrastructure.fcm_client import FCMClient, PushPayload


@patch("firebase_admin.messaging.send", return_value="projects/test/messages/abc123")
@patch(
    "features.accounts.infrastructure.firebase_apps.ensure_firebase_app",
    return_value=MagicMock(name="firebase-app"),
)
def test_fcm_client_send_mock(mock_ensure_app, mock_send):
    client = FCMClient(credentials_path="/tmp/fake-service-account.json")
    message_id = client.send(
        token="device-token-xyz",
        title="Pedido en camino",
        body="¡Tu pedido ya salió! Va en camino",
        data={"notification_type": "order_on_the_way", "order_id": "42"},
    )

    mock_ensure_app.assert_called_once_with("customer")
    mock_send.assert_called_once()

    sent_message = mock_send.call_args.args[0]
    assert sent_message.token == "device-token-xyz"
    assert sent_message.notification.title == "Pedido en camino"
    assert sent_message.notification.body == "¡Tu pedido ya salió! Va en camino"
    assert sent_message.data == {
        "notification_type": "order_on_the_way",
        "order_id": "42",
    }
    assert message_id == "projects/test/messages/abc123"


@patch("firebase_admin.messaging.send", return_value="projects/test/messages/def456")
@patch(
    "features.accounts.infrastructure.firebase_apps.ensure_firebase_app",
    return_value=MagicMock(name="firebase-app"),
)
def test_fcm_client_send_payload(mock_ensure_app, mock_send):
    client = FCMClient(credentials_path="/tmp/fake-service-account.json")
    payload = PushPayload(
        token="another-token",
        title="Pedido aceptado",
        body="Tu pedido fue aceptado",
    )

    assert client.send_payload(payload) == "projects/test/messages/def456"
    mock_send.assert_called_once()
    mock_ensure_app.assert_called_once()


@patch(
    "features.accounts.infrastructure.firebase_apps.ensure_firebase_app",
    side_effect=FCMNotConfiguredError("Credenciales Firebase no configuradas"),
)
def test_fcm_client_requires_credentials(mock_ensure_app):
    client = FCMClient(credentials_path=None)

    with pytest.raises(FCMNotConfiguredError, match="Credenciales Firebase"):
        client.send(token="t", title="T", body="B")

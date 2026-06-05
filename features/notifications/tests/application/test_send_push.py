from unittest.mock import MagicMock

from features.notifications.application.dto import SendPushDTO
from features.notifications.application.use_cases.send_push import SendPushUseCase
from features.orders.domain.value_objects import OrderStatus


def test_send_push_use_case_calls_fcm_for_each_token():
    fcm_client = MagicMock()
    fcm_client.send.side_effect = ["msg-1", "msg-2"]
    device_token_repository = MagicMock()
    device_token_repository.list_active_tokens_for_user.return_value = [
        "token-a",
        "token-b",
    ]

    use_case = SendPushUseCase(
        device_token_repository=device_token_repository,
        fcm_client=fcm_client,
    )

    message_ids = use_case.execute(
        SendPushDTO(
            user_id=10,
            order_id=42,
            order_status=OrderStatus.ACCEPTED_BY_MERCHANT,
        )
    )

    assert message_ids == ["msg-1", "msg-2"]
    assert fcm_client.send.call_count == 2
    fcm_client.send.assert_any_call(
        token="token-a",
        title="Pedido aceptado",
        body="Tu pedido fue aceptado",
        data={
            "notification_type": "order_accepted",
            "order_id": "42",
            "order_status": "accepted_by_merchant",
        },
    )


def test_send_push_use_case_returns_empty_when_no_tokens():
    fcm_client = MagicMock()
    device_token_repository = MagicMock()
    device_token_repository.list_active_tokens_for_user.return_value = []

    use_case = SendPushUseCase(
        device_token_repository=device_token_repository,
        fcm_client=fcm_client,
    )

    message_ids = use_case.execute(
        SendPushDTO(
            user_id=10,
            order_id=42,
            order_status=OrderStatus.ON_THE_WAY,
        )
    )

    assert message_ids == []
    fcm_client.send.assert_not_called()

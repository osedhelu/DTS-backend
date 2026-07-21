from unittest.mock import MagicMock

from features.notifications.application.dto import SendChatPushDTO
from features.notifications.application.use_cases.send_push import SendPushUseCase
from features.notifications.domain.entities import NotificationType


def test_execute_chat_sends_payload_with_chat_type():
    token_repo = MagicMock()
    token_repo.list_active_tokens_for_user.return_value = ["tok-1"]
    fcm = MagicMock()
    fcm.send.return_value = "mid-1"

    use_case = SendPushUseCase(device_token_repository=token_repo, fcm_client=fcm)
    ids = use_case.execute_chat(
        SendChatPushDTO(
            user_id=10,
            order_id=42,
            preview="Hola, voy en camino",
            sender_role="driver",
        )
    )

    assert ids == ["mid-1"]
    fcm.send.assert_called_once()
    kwargs = fcm.send.call_args.kwargs
    assert kwargs["title"] == "Nuevo mensaje"
    assert "camino" in kwargs["body"]
    assert kwargs["data"]["type"] == NotificationType.CHAT_MESSAGE.value
    assert kwargs["data"]["order_id"] == "42"


def test_execute_chat_without_tokens_returns_empty():
    token_repo = MagicMock()
    token_repo.list_active_tokens_for_user.return_value = []
    fcm = MagicMock()

    use_case = SendPushUseCase(device_token_repository=token_repo, fcm_client=fcm)
    ids = use_case.execute_chat(
        SendChatPushDTO(user_id=10, order_id=42, preview="Hola")
    )

    assert ids == []
    fcm.send.assert_not_called()

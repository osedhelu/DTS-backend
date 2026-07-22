from unittest.mock import MagicMock

import pytest

from features.notifications.application.dto import SendPushDTO
from features.notifications.application.use_cases.send_push import SendPushUseCase
from features.notifications.infrastructure.tasks import _empty_recipients_reason
from features.orders.domain.value_objects import OrderStatus
from features.stores.domain.value_objects import GeoLocation


def test_execute_without_tokens_returns_empty_and_skips_fcm(caplog):
    token_repo = MagicMock()
    token_repo.list_active_tokens_for_user.return_value = []
    fcm = MagicMock()

    use_case = SendPushUseCase(device_token_repository=token_repo, fcm_client=fcm)
    with caplog.at_level("INFO"):
        ids = use_case.execute(
            SendPushDTO(
                user_id=5,
                order_id=99,
                order_status=OrderStatus.ACCEPTED_BY_MERCHANT,
            )
        )

    assert ids == []
    fcm.send.assert_not_called()
    assert any("push_no_device_token" in r.message for r in caplog.records)


def test_execute_with_tokens_logs_push_sent(caplog):
    token_repo = MagicMock()
    token_repo.list_active_tokens_for_user.return_value = ["tok-a"]
    fcm = MagicMock()
    fcm.send.return_value = "mid-1"

    use_case = SendPushUseCase(device_token_repository=token_repo, fcm_client=fcm)
    with caplog.at_level("INFO"):
        ids = use_case.execute(
            SendPushDTO(
                user_id=5,
                order_id=99,
                order_status=OrderStatus.IN_PREPARATION,
            )
        )

    assert ids == ["mid-1"]
    assert any("push_sent" in r.message for r in caplog.records)


@pytest.mark.parametrize(
    ("status", "pickup", "expected"),
    [
        (OrderStatus.READY_FOR_PICKUP, None, "no_store_location"),
        (
            OrderStatus.READY_FOR_PICKUP,
            GeoLocation(latitude=4.7, longitude=-74.0),
            "no_online_drivers_in_radius",
        ),
        (OrderStatus.ACCEPTED_BY_MERCHANT, None, "no_customer"),
    ],
)
def test_empty_recipients_reason(status, pickup, expected):
    assert _empty_recipients_reason(status, pickup) == expected

from features.notifications.application.dto import SendPushDTO
from features.notifications.domain.entities import PushTemplate
from features.notifications.domain.repositories import (
    DeviceTokenRepository,
    PushNotificationClient,
)


class SendPushUseCase:
    def __init__(
        self,
        device_token_repository: DeviceTokenRepository,
        fcm_client: PushNotificationClient,
    ) -> None:
        self._device_token_repository = device_token_repository
        self._fcm_client = fcm_client

    def execute(self, dto: SendPushDTO) -> list[str]:
        template = PushTemplate.for_status(dto.order_status)
        tokens = self._device_token_repository.list_active_tokens_for_user(dto.user_id)
        if not tokens:
            return []

        data = {
            "notification_type": template.notification_type.value,
            "order_id": str(dto.order_id),
            "order_status": dto.order_status.value,
        }

        message_ids: list[str] = []
        for token in tokens:
            message_id = self._fcm_client.send(
                token=token,
                title=template.title,
                body=template.body,
                data=data,
            )
            message_ids.append(message_id)

        return message_ids

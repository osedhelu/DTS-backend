from features.notifications.application.dto import SendChatPushDTO, SendPushDTO
from features.notifications.domain.entities import NotificationType, PushTemplate
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
            # Contrato Flutter (docs/FLUTTER_API.md): type = OrderStatus
            "type": dto.order_status.value,
            "order_id": str(dto.order_id),
            "order_status": dto.order_status.value,
        }

        title = dto.title_override or template.title
        body = dto.body_override or template.body

        message_ids: list[str] = []
        for token in tokens:
            message_id = self._fcm_client.send(
                token=token,
                title=title,
                body=body,
                data=data,
            )
            message_ids.append(message_id)

        return message_ids

    def execute_chat(self, dto: SendChatPushDTO) -> list[str]:
        tokens = self._device_token_repository.list_active_tokens_for_user(dto.user_id)
        if not tokens:
            return []

        preview = (dto.preview or "").strip()[:120] or "Tienes un mensaje sobre tu pedido"
        data = {
            "notification_type": NotificationType.CHAT_MESSAGE.value,
            "type": NotificationType.CHAT_MESSAGE.value,
            "order_id": str(dto.order_id),
            "preview": preview[:100],
            "sender_role": dto.sender_role or "",
        }
        title = "Nuevo mensaje"
        body = preview

        message_ids: list[str] = []
        for token in tokens:
            message_ids.append(
                self._fcm_client.send(
                    token=token,
                    title=title,
                    body=body,
                    data=data,
                )
            )
        return message_ids

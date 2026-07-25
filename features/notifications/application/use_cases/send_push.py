import logging

from features.notifications.application.dto import SendChatPushDTO, SendPushDTO
from features.notifications.domain.entities import NotificationType, PushTemplate
from features.notifications.domain.exceptions import FCMSendError
from features.notifications.domain.repositories import (
    DeviceTokenRepository,
    PushNotificationClient,
)

logger = logging.getLogger(__name__)

_STALE_TOKEN_MARKERS = (
    "unregistered",
    "notregistered",
    "not registered",
    "senderid mismatch",
    "sender id mismatch",
    "registration-token-not-registered",
    "requested entity was not found",
)

# FCM reporta APNs mal configurado como ThirdPartyAuthError/401 engañoso.
_SKIPPABLE_PLATFORM_MARKERS = (
    "thirdpartyautherror",
    "missing required authentication credential",
    "auth error from apns",
    "apns certificate",
)


def _is_stale_token_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(marker in msg for marker in _STALE_TOKEN_MARKERS)


def _is_skippable_platform_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(marker in msg for marker in _SKIPPABLE_PLATFORM_MARKERS)


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
            logger.info(
                "push_no_device_token user_id=%s order_id=%s status=%s",
                dto.user_id,
                dto.order_id,
                dto.order_status.value,
            )
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

        message_ids = self._send_to_tokens(
            tokens,
            title=title,
            body=body,
            data=data,
            log_prefix="push",
            user_id=dto.user_id,
            order_id=dto.order_id,
            extra_log=f"status={dto.order_status.value}",
        )
        return message_ids

    def execute_chat(self, dto: SendChatPushDTO) -> list[str]:
        tokens = self._device_token_repository.list_active_tokens_for_user(dto.user_id)
        if not tokens:
            logger.info(
                "chat_push_no_device_token user_id=%s order_id=%s",
                dto.user_id,
                dto.order_id,
            )
            return []

        preview = (dto.preview or "").strip()[:120] or "Tienes un mensaje sobre tu pedido"
        data = {
            "notification_type": NotificationType.CHAT_MESSAGE.value,
            "type": NotificationType.CHAT_MESSAGE.value,
            "order_id": str(dto.order_id),
            "preview": preview[:100],
            "sender_role": dto.sender_role or "",
        }
        return self._send_to_tokens(
            tokens,
            title="Nuevo mensaje",
            body=preview,
            data=data,
            log_prefix="chat_push",
            user_id=dto.user_id,
            order_id=dto.order_id,
        )

    def _send_to_tokens(
        self,
        tokens: list[str],
        *,
        title: str,
        body: str,
        data: dict[str, str],
        log_prefix: str,
        user_id: int,
        order_id: int,
        extra_log: str = "",
    ) -> list[str]:
        message_ids: list[str] = []
        last_error: FCMSendError | None = None

        for token in tokens:
            try:
                message_ids.append(
                    self._fcm_client.send(
                        token=token,
                        title=title,
                        body=body,
                        data=data,
                    )
                )
            except FCMSendError as exc:
                last_error = exc
                if _is_stale_token_error(exc):
                    logger.warning(
                        "%s_stale_token user_id=%s order_id=%s error=%s",
                        log_prefix,
                        user_id,
                        order_id,
                        exc,
                    )
                    self._device_token_repository.deactivate_token(token)
                    continue
                if _is_skippable_platform_error(exc):
                    logger.warning(
                        "%s_platform_auth_skip user_id=%s order_id=%s "
                        "hint=check_apns_key_in_firebase error=%s",
                        log_prefix,
                        user_id,
                        order_id,
                        exc,
                    )
                    continue
                logger.warning(
                    "%s_token_failed user_id=%s order_id=%s error=%s",
                    log_prefix,
                    user_id,
                    order_id,
                    exc,
                )

        if message_ids:
            logger.info(
                "%s_sent user_id=%s order_id=%s %stokens=%s message_ids=%s",
                log_prefix,
                user_id,
                order_id,
                f"{extra_log} " if extra_log else "",
                len(tokens),
                len(message_ids),
            )
            return message_ids

        if last_error is not None:
            raise last_error

        logger.info(
            "%s_no_success user_id=%s order_id=%s tokens=%s",
            log_prefix,
            user_id,
            order_id,
            len(tokens),
        )
        return []

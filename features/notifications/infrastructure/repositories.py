from features.accounts.infrastructure.models import CustomUser, DeviceToken


class DjangoCustomerEmailRepository:
    def get_email_for_user(self, user_id: int) -> str | None:
        return (
            CustomUser.objects.filter(pk=user_id)
            .values_list("email", flat=True)
            .first()
        )


class DjangoDeviceTokenRepository:
    def list_active_tokens_for_user(self, user_id: int) -> list[str]:
        # Más recientes primero: tokens viejos suelen estar Unregistered.
        return list(
            DeviceToken.objects.filter(user_id=user_id, is_active=True)
            .order_by("-id")
            .values_list("token", flat=True)
        )

    def deactivate_token(self, token: str) -> None:
        DeviceToken.objects.filter(token=token, is_active=True).update(is_active=False)

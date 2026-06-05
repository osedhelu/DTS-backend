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
        return list(
            DeviceToken.objects.filter(user_id=user_id, is_active=True).values_list(
                "token", flat=True
            )
        )

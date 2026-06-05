from features.accounts.infrastructure.models import DeviceToken


class DjangoDeviceTokenRepository:
    def list_active_tokens_for_user(self, user_id: int) -> list[str]:
        return list(
            DeviceToken.objects.filter(user_id=user_id, is_active=True).values_list(
                "token", flat=True
            )
        )

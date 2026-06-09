from datetime import datetime

from django.utils import timezone

from features.accounts.domain.exceptions import PasswordResetTokenNotFoundError
from features.accounts.domain.repositories import PasswordResetTokenRepository
from features.accounts.infrastructure.models import CustomUser


class ConfirmPasswordResetUseCase:
    def __init__(self, token_repository: PasswordResetTokenRepository) -> None:
        self._token_repository = token_repository

    def execute(
        self,
        token_value: str,
        new_password: str,
        now: datetime | None = None,
    ) -> CustomUser:
        now = now or timezone.now()
        token = self._token_repository.get_by_token(token_value)
        if token is None:
            raise PasswordResetTokenNotFoundError("Enlace de recuperación inválido")

        token.validate_for_use(now)

        user = CustomUser.objects.get(pk=token.user_id)
        user.set_password(new_password)
        user.save(update_fields=["password"])
        self._token_repository.mark_used(token.id, now)
        return user

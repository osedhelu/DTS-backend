from datetime import datetime

from django.utils import timezone

from features.accounts.domain.exceptions import (
    EmailAlreadyVerifiedError,
    VerificationTokenNotFoundError,
)
from features.accounts.domain.repositories import EmailVerificationTokenRepository
from features.accounts.infrastructure.models import CustomUser


class VerifyEmailUseCase:
    def __init__(self, token_repository: EmailVerificationTokenRepository) -> None:
        self._token_repository = token_repository

    def execute(self, token_value: str, now: datetime | None = None) -> CustomUser:
        now = now or timezone.now()
        token = self._token_repository.get_by_token(token_value)
        if token is None:
            raise VerificationTokenNotFoundError("Token de verificación inválido")

        token.validate_for_use(now)

        user = CustomUser.objects.get(pk=token.user_id)
        if user.email_verified:
            raise EmailAlreadyVerifiedError("El email ya fue verificado")

        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])
        self._token_repository.mark_used(token.id, now)
        return user

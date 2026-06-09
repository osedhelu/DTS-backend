from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from features.accounts.domain.repositories import PasswordResetTokenRepository
from features.accounts.domain.value_objects import Email
from features.accounts.infrastructure.models import CustomUser

TOKEN_TTL = timedelta(hours=1)

GENERIC_SUCCESS_MESSAGE = (
    "Si el email está registrado, recibirás un enlace para restablecer tu contraseña"
)


@dataclass(frozen=True)
class PasswordResetRequestResult:
    message: str
    user_id: int | None = None
    token: str | None = None


class RequestPasswordResetUseCase:
    def __init__(self, token_repository: PasswordResetTokenRepository) -> None:
        self._token_repository = token_repository

    def execute(self, email_value: str) -> PasswordResetRequestResult:
        email = Email(email_value)

        try:
            user = CustomUser.objects.get(email__iexact=email.value)
        except CustomUser.DoesNotExist:
            return PasswordResetRequestResult(message=GENERIC_SUCCESS_MESSAGE)

        expires_at = timezone.now() + TOKEN_TTL
        token = self._token_repository.create(user.id, expires_at)

        return PasswordResetRequestResult(
            message=GENERIC_SUCCESS_MESSAGE,
            user_id=user.id,
            token=token.token,
        )

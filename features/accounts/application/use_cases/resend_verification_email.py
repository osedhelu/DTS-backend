from datetime import timedelta

from django.utils import timezone

from features.accounts.domain.entities import UserRole
from features.accounts.domain.exceptions import EmailAlreadyVerifiedError
from features.accounts.domain.repositories import EmailVerificationTokenRepository
from features.accounts.domain.value_objects import Email
from features.accounts.infrastructure.models import CustomUser

TOKEN_TTL = timedelta(hours=24)


class ResendVerificationEmailUseCase:
    def __init__(self, token_repository: EmailVerificationTokenRepository) -> None:
        self._token_repository = token_repository

    def execute(self, email_value: str) -> tuple[CustomUser, str] | None:
        email = Email(email_value)
        try:
            user = CustomUser.objects.get(email=email.value, role=UserRole.MERCHANT)
        except CustomUser.DoesNotExist:
            return None

        if user.email_verified:
            raise EmailAlreadyVerifiedError("El email ya fue verificado")

        expires_at = timezone.now() + TOKEN_TTL
        token = self._token_repository.create(user.id, expires_at)
        return user, token.token

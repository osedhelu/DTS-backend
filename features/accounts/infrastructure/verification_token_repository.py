from datetime import datetime

from features.accounts.domain.repositories import EmailVerificationTokenRepository
from features.accounts.domain.verification_token import EmailVerificationToken
from features.accounts.infrastructure.models import EmailVerificationToken as EmailVerificationTokenModel


def _to_entity(model: EmailVerificationTokenModel) -> EmailVerificationToken:
    return EmailVerificationToken(
        id=model.id,
        user_id=model.user_id,
        token=str(model.token),
        expires_at=model.expires_at,
        used_at=model.used_at,
    )


class DjangoEmailVerificationTokenRepository(EmailVerificationTokenRepository):
    def create(self, user_id: int, expires_at: datetime) -> EmailVerificationToken:
        model = EmailVerificationTokenModel.objects.create(
            user_id=user_id,
            expires_at=expires_at,
        )
        return _to_entity(model)

    def get_by_token(self, token: str) -> EmailVerificationToken | None:
        try:
            model = EmailVerificationTokenModel.objects.get(token=token)
        except EmailVerificationTokenModel.DoesNotExist:
            return None
        return _to_entity(model)

    def mark_used(self, token_id: int, used_at: datetime) -> None:
        EmailVerificationTokenModel.objects.filter(pk=token_id).update(used_at=used_at)

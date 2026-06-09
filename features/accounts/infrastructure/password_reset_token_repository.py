from datetime import datetime

from features.accounts.domain.password_reset_token import PasswordResetToken
from features.accounts.domain.repositories import PasswordResetTokenRepository
from features.accounts.infrastructure.models import PasswordResetToken as PasswordResetTokenModel


def _to_entity(model: PasswordResetTokenModel) -> PasswordResetToken:
    return PasswordResetToken(
        id=model.id,
        user_id=model.user_id,
        token=str(model.token),
        expires_at=model.expires_at,
        used_at=model.used_at,
    )


class DjangoPasswordResetTokenRepository(PasswordResetTokenRepository):
    def create(self, user_id: int, expires_at: datetime) -> PasswordResetToken:
        self.invalidate_unused_for_user(user_id)
        model = PasswordResetTokenModel.objects.create(
            user_id=user_id,
            expires_at=expires_at,
        )
        return _to_entity(model)

    def get_by_token(self, token: str) -> PasswordResetToken | None:
        try:
            model = PasswordResetTokenModel.objects.get(token=token)
        except PasswordResetTokenModel.DoesNotExist:
            return None
        return _to_entity(model)

    def mark_used(self, token_id: int, used_at: datetime) -> None:
        PasswordResetTokenModel.objects.filter(pk=token_id).update(used_at=used_at)

    def invalidate_unused_for_user(self, user_id: int) -> None:
        PasswordResetTokenModel.objects.filter(user_id=user_id, used_at__isnull=True).delete()

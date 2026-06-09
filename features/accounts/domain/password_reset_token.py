from dataclasses import dataclass
from datetime import datetime

from features.accounts.domain.exceptions import (
    PasswordResetTokenAlreadyUsedError,
    PasswordResetTokenExpiredError,
)


@dataclass
class PasswordResetToken:
    user_id: int
    token: str
    expires_at: datetime
    id: int | None = None
    used_at: datetime | None = None

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def is_used(self) -> bool:
        return self.used_at is not None

    def validate_for_use(self, now: datetime) -> None:
        if self.is_used():
            raise PasswordResetTokenAlreadyUsedError(
                "El enlace de recuperación ya fue utilizado"
            )
        if self.is_expired(now):
            raise PasswordResetTokenExpiredError(
                "El enlace de recuperación ha expirado"
            )

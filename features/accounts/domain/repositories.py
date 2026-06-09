from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Protocol

from features.accounts.domain.password_reset_token import PasswordResetToken
from features.accounts.domain.verification_token import EmailVerificationToken


class UserRepository(Protocol):
    def exists_by_email(self, email: str) -> bool: ...

    def register(self, data: dict[str, Any]) -> Any: ...


class EmailVerificationTokenRepository(ABC):
    @abstractmethod
    def create(self, user_id: int, expires_at: datetime) -> EmailVerificationToken:
        pass

    @abstractmethod
    def get_by_token(self, token: str) -> EmailVerificationToken | None:
        pass

    @abstractmethod
    def mark_used(self, token_id: int, used_at: datetime) -> None:
        pass


class PasswordResetTokenRepository(ABC):
    @abstractmethod
    def create(self, user_id: int, expires_at: datetime) -> PasswordResetToken:
        pass

    @abstractmethod
    def get_by_token(self, token: str) -> PasswordResetToken | None:
        pass

    @abstractmethod
    def mark_used(self, token_id: int, used_at: datetime) -> None:
        pass

    @abstractmethod
    def invalidate_unused_for_user(self, user_id: int) -> None:
        pass

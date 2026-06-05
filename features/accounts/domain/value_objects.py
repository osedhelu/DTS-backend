import re
from dataclasses import dataclass

from features.accounts.domain.exceptions import InvalidEmailError, InvalidPhoneError

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(r"^\+\d{10,15}$")


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise InvalidEmailError(f"Email inválido: {self.value!r}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Phone:
    value: str

    def __post_init__(self) -> None:
        cleaned = re.sub(r"[\s\-().]", "", self.value.strip())
        if not PHONE_PATTERN.match(cleaned):
            raise InvalidPhoneError(
                f"Teléfono inválido: {self.value!r}. Use formato E.164 (+573001234567)"
            )
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value

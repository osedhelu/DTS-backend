from typing import Any, Protocol


class UserRepository(Protocol):
    def exists_by_email(self, email: str) -> bool: ...

    def register(self, data: dict[str, Any]) -> Any: ...

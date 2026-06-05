from typing import Protocol


class DeviceTokenRepository(Protocol):
    def list_active_tokens_for_user(self, user_id: int) -> list[str]: ...


class PushNotificationClient(Protocol):
    def send(
        self,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> str: ...

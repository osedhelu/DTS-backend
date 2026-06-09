from typing import Any, Protocol

from features.stores.domain.entities import Store, StoreStatus


class StoreRepository(Protocol):
    def create(self, data: dict[str, Any]) -> Store: ...

    def get_by_id(self, store_id: int) -> Store | None: ...

    def list_all(
        self,
        status: StoreStatus | None = None,
        *,
        active_only: bool = True,
    ) -> list[Store]: ...

    def list_by_owner(
        self,
        owner_id: int,
        *,
        active_only: bool = False,
    ) -> list[Store]: ...

    def set_active(self, store_id: int, is_active: bool) -> Store: ...

    def update_status(self, store_id: int, status: StoreStatus) -> Store: ...

    def update_profile(
        self,
        store_id: int,
        data: dict,
        logo_file: object | None = None,
        location: object | None = None,
    ) -> Store: ...

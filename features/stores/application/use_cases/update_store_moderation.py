from features.stores.domain.exceptions import StoreNotFoundError
from features.stores.domain.repositories import StoreRepository


class UpdateStoreModerationUseCase:
    def __init__(self, store_repository: StoreRepository) -> None:
        self._store_repository = store_repository

    def execute(self, store_id: int, is_active: bool):
        store = self._store_repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {store_id} no encontrado")

        return self._store_repository.set_active(store_id, is_active)

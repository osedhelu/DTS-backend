from features.stores.application.dto import UpdateStoreStatusDTO
from features.stores.domain.entities import StoreStatus
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.domain.repositories import StoreRepository


class UpdateStoreStatusUseCase:
    def __init__(self, store_repository: StoreRepository) -> None:
        self._store_repository = store_repository

    def execute(self, dto: UpdateStoreStatusDTO):
        store = self._store_repository.get_by_id(dto.store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {dto.store_id} no encontrado")

        if store.owner_id != dto.owner_id:
            raise NotStoreOwnerError("No tienes permiso para modificar este comercio")

        return self._store_repository.update_status(dto.store_id, dto.status)

    def close(self, store_id: int, owner_id: int):
        return self.execute(
            UpdateStoreStatusDTO(
                store_id=store_id,
                owner_id=owner_id,
                status=StoreStatus.CLOSED,
            )
        )

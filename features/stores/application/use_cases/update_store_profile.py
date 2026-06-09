from features.stores.application.dto import UpdateStoreProfileDTO
from features.stores.domain.entities import StoreStatus
from features.stores.domain.exceptions import (
    DomainValidationError,
    NotStoreOwnerError,
    StoreNotFoundError,
)
from features.stores.domain.repositories import StoreRepository
from features.stores.domain.value_objects import GeoLocation


class UpdateStoreProfileUseCase:
    def __init__(self, store_repository: StoreRepository) -> None:
        self._store_repository = store_repository

    def execute(self, dto: UpdateStoreProfileDTO):
        store = self._store_repository.get_by_id(dto.store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {dto.store_id} no encontrado")

        if store.owner_id != dto.owner_id:
            raise NotStoreOwnerError("No tienes permiso para modificar este comercio")

        updates: dict[str, object] = {}

        if dto.name is not None:
            name = dto.name.strip()
            if not name:
                raise DomainValidationError("El nombre de la tienda es obligatorio")
            updates["name"] = name

        if dto.description is not None:
            updates["description"] = dto.description.strip()

        if dto.phone is not None:
            updates["phone"] = dto.phone.strip()

        if dto.address is not None:
            updates["address"] = dto.address.strip()

        location: GeoLocation | None = None
        if dto.latitude is not None and dto.longitude is not None:
            location = GeoLocation(latitude=dto.latitude, longitude=dto.longitude)

        if dto.status is not None:
            updates["status"] = dto.status.value

        if not updates and dto.logo_file is None and location is None:
            raise DomainValidationError("No hay cambios para guardar")

        return self._store_repository.update_profile(
            dto.store_id,
            updates,
            logo_file=dto.logo_file,
            location=location,
        )

    def get_profile(self, store_id: int, owner_id: int):
        store = self._store_repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {store_id} no encontrado")

        if store.owner_id != owner_id:
            raise NotStoreOwnerError("No tienes permiso para ver este comercio")

        return store

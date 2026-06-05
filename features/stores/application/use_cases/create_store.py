from features.stores.application.dto import CreateStoreDTO
from features.stores.domain.repositories import StoreRepository
from features.stores.domain.value_objects import GeoLocation


class CreateStoreUseCase:
    def __init__(self, store_repository: StoreRepository) -> None:
        self._store_repository = store_repository

    def execute(self, dto: CreateStoreDTO):
        geo = GeoLocation(latitude=dto.latitude, longitude=dto.longitude)

        return self._store_repository.create(
            {
                "owner_id": dto.owner_id,
                "name": dto.name.strip(),
                "latitude": geo.latitude,
                "longitude": geo.longitude,
                "address": dto.address,
                "status": dto.status,
            }
        )

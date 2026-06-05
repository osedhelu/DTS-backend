from features.stores.domain.entities import Store, StoreStatus
from features.stores.domain.value_objects import GeoLocation
from features.stores.infrastructure.models import Store as StoreModel


def _to_entity(model: StoreModel) -> Store:
    return Store(
        id=model.id,
        name=model.name,
        owner_id=model.owner_id,
        status=StoreStatus(model.status),
        latitude=model.latitude,
        longitude=model.longitude,
        address=model.address,
    )


class DjangoStoreRepository:
    def create(self, data: dict) -> Store:
        store = StoreModel(
            owner_id=data["owner_id"],
            name=data["name"],
            status=data["status"],
            address=data.get("address", ""),
        )
        store.set_location(
            GeoLocation(latitude=data["latitude"], longitude=data["longitude"])
        )
        store.save()
        return _to_entity(store)

    def get_by_id(self, store_id: int) -> Store | None:
        try:
            return _to_entity(StoreModel.objects.get(pk=store_id))
        except StoreModel.DoesNotExist:
            return None

    def list_all(self) -> list[Store]:
        return [_to_entity(model) for model in StoreModel.objects.all().order_by("name")]

    def update_status(self, store_id: int, status: StoreStatus) -> Store:
        model = StoreModel.objects.get(pk=store_id)
        model.status = status
        model.save(update_fields=["status", "updated_at"])
        return _to_entity(model)

from features.stores.domain.entities import Store, StoreStatus, StoreVertical
from features.stores.domain.value_objects import GeoLocation
from features.stores.infrastructure.models import Store as StoreModel


def _to_entity(model: StoreModel) -> Store:
    return Store(
        id=model.id,
        name=model.name,
        owner_id=model.owner_id,
        status=StoreStatus(model.status),
        vertical=StoreVertical(model.vertical),
        latitude=model.latitude,
        longitude=model.longitude,
        address=model.address,
        description=model.description,
        phone=model.phone,
        logo_url=model.logo.url if model.logo else "",
    )


class DjangoStoreRepository:
    def create(self, data: dict) -> Store:
        store = StoreModel(
            owner_id=data["owner_id"],
            name=data["name"],
            status=data["status"],
            address=data.get("address", ""),
            vertical=data.get("vertical", StoreVertical.FOOD),
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

    def list_all(self, status: StoreStatus | None = None) -> list[Store]:
        queryset = StoreModel.objects.all().order_by("name")
        if status is not None:
            queryset = queryset.filter(status=status.value)
        return [_to_entity(model) for model in queryset]

    def update_status(self, store_id: int, status: StoreStatus) -> Store:
        model = StoreModel.objects.get(pk=store_id)
        model.status = status
        model.save(update_fields=["status", "updated_at"])
        return _to_entity(model)

    def update_profile(
        self,
        store_id: int,
        data: dict,
        logo_file: object | None = None,
    ) -> Store:
        model = StoreModel.objects.get(pk=store_id)
        update_fields = ["updated_at"]

        for field, value in data.items():
            setattr(model, field, value)
            update_fields.append(field)

        if logo_file is not None:
            model.logo = logo_file
            update_fields.append("logo")

        model.save(update_fields=update_fields)
        return _to_entity(model)

from features.products.application.category_templates import (
    CategoryTemplateAlreadyImportedError,
    CategoryTemplateNotFoundError,
    import_store_category_template,
    list_category_templates,
)
from features.products.infrastructure.models import Category
from features.stores.domain.entities import StoreVertical
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.domain.repositories import StoreRepository


class ImportCategoryTemplateUseCase:
    def __init__(self, store_repository: StoreRepository) -> None:
        self._store_repository = store_repository

    def list_templates(
        self,
        *,
        store_id: int,
        owner_id: int,
        query: str = "",
    ) -> dict:
        store = self._ensure_store_owner(store_id, owner_id)
        vertical = StoreVertical(store.vertical)
        imported_names = set(
            Category.objects.filter(store_id=store_id, parent__isnull=True).values_list(
                "name",
                flat=True,
            )
        )
        return {
            "vertical": vertical.value,
            "templates": list_category_templates(
                vertical,
                query=query,
                imported_root_names=imported_names,
            ),
        }

    def execute(
        self,
        *,
        store_id: int,
        owner_id: int,
        template_name: str,
    ) -> dict:
        store = self._ensure_store_owner(store_id, owner_id)
        vertical = StoreVertical(store.vertical)
        return import_store_category_template(store_id, vertical, template_name)

    def _ensure_store_owner(self, store_id: int, owner_id: int):
        store = self._store_repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {store_id} no encontrado")
        if store.owner_id != owner_id:
            raise NotStoreOwnerError("No tienes permiso para modificar este comercio")
        return store

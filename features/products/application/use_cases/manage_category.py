from features.products.application.dto import (
    CreateCategoryDTO,
    CreateSubcategoryDTO,
    DeleteCategoryDTO,
    UpdateCategoryDTO,
)
from features.products.domain.entities import Category
from features.products.domain.exceptions import (
    CategoryInUseError,
    CategoryNotFoundError,
    InvalidCategoryHierarchyError,
)
from features.products.domain.repositories import CategoryRepository
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.domain.repositories import StoreRepository


class CreateCategoryUseCase:
    def __init__(
        self,
        category_repository: CategoryRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._category_repository = category_repository
        self._store_repository = store_repository

    def execute(self, dto: CreateCategoryDTO) -> Category:
        self._ensure_store_owner(dto.store_id, dto.owner_id)

        return self._category_repository.create(
            {
                "name": dto.name.strip(),
                "store_id": dto.store_id,
                "parent_id": None,
            }
        )

    def _ensure_store_owner(self, store_id: int, owner_id: int) -> None:
        store = self._store_repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {store_id} no encontrado")
        if store.owner_id != owner_id:
            raise NotStoreOwnerError("No tienes permiso para modificar este comercio")


class CreateSubcategoryUseCase(CreateCategoryUseCase):
    def execute(self, dto: CreateSubcategoryDTO) -> Category:
        self._ensure_store_owner(dto.store_id, dto.owner_id)

        parent = self._category_repository.get_by_id(dto.parent_id)
        if parent is None or parent.store_id != dto.store_id:
            raise CategoryNotFoundError(f"Categoría padre {dto.parent_id} no encontrada")
        if parent.is_subcategory:
            raise InvalidCategoryHierarchyError(
                "Solo se permiten subcategorías bajo una categoría raíz"
            )

        return self._category_repository.create(
            {
                "name": dto.name.strip(),
                "store_id": dto.store_id,
                "parent_id": dto.parent_id,
            }
        )


class UpdateCategoryUseCase(CreateCategoryUseCase):
    def execute(self, dto: UpdateCategoryDTO) -> Category:
        self._ensure_store_owner(dto.store_id, dto.owner_id)

        category = self._category_repository.get_by_id(dto.category_id)
        if category is None or category.store_id != dto.store_id:
            raise CategoryNotFoundError(f"Categoría {dto.category_id} no encontrada")

        name = dto.name.strip()
        if not name:
            raise InvalidCategoryHierarchyError("El nombre de la categoría es obligatorio")

        return self._category_repository.update(
            dto.category_id,
            {"name": name},
        )


class DeleteCategoryUseCase(CreateCategoryUseCase):
    def execute(self, dto: DeleteCategoryDTO) -> None:
        self._ensure_store_owner(dto.store_id, dto.owner_id)

        category = self._category_repository.get_by_id(dto.category_id)
        if category is None or category.store_id != dto.store_id:
            raise CategoryNotFoundError(f"Categoría {dto.category_id} no encontrada")

        if self._category_repository.count_products(dto.category_id) > 0:
            raise CategoryInUseError(
                "No se puede eliminar: hay productos asociados a esta categoría"
            )

        if not category.is_subcategory and self._category_repository.count_subcategories(
            dto.category_id
        ) > 0:
            raise CategoryInUseError(
                "Elimina primero las subcategorías de esta categoría"
            )

        self._category_repository.delete(dto.category_id)

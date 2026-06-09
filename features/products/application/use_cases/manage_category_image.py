from features.products.application.dto import (
    DeleteCategoryImageDTO,
    UpdateCategoryImageDTO,
    UploadCategoryImageDTO,
)
from features.products.domain.entities import CategoryImage
from features.products.domain.exceptions import (
    CategoryImageNotFoundError,
    CategoryNotFoundError,
    DomainValidationError,
)
from features.products.domain.repositories import CategoryRepository
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.domain.repositories import StoreRepository


class _CategoryOwnershipMixin:
    _category_repository: CategoryRepository
    _store_repository: StoreRepository

    def _get_owned_category(self, store_id: int, category_id: int, owner_id: int):
        category = self._category_repository.get_by_id(category_id)
        if category is None or category.store_id != store_id:
            raise CategoryNotFoundError(f"Categoría {category_id} no encontrada")

        store = self._store_repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {store_id} no encontrado")
        if store.owner_id != owner_id:
            raise NotStoreOwnerError("No tienes permiso para modificar este comercio")
        return category


class UploadCategoryImageUseCase(_CategoryOwnershipMixin):
    def __init__(
        self,
        category_repository: CategoryRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._category_repository = category_repository
        self._store_repository = store_repository

    def execute(self, dto: UploadCategoryImageDTO) -> CategoryImage:
        self._get_owned_category(dto.store_id, dto.category_id, dto.owner_id)
        return self._category_repository.add_image(
            dto.category_id,
            dto.image_file,
            is_primary=dto.is_primary,
        )


class DeleteCategoryImageUseCase(_CategoryOwnershipMixin):
    def __init__(
        self,
        category_repository: CategoryRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._category_repository = category_repository
        self._store_repository = store_repository

    def execute(self, dto: DeleteCategoryImageDTO) -> None:
        self._get_owned_category(dto.store_id, dto.category_id, dto.owner_id)
        image = self._category_repository.get_image(dto.image_id)
        if image is None or image.category_id != dto.category_id:
            raise CategoryImageNotFoundError("Imagen no encontrada")
        self._category_repository.delete_image(dto.image_id)


class UpdateCategoryImageUseCase(_CategoryOwnershipMixin):
    def __init__(
        self,
        category_repository: CategoryRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._category_repository = category_repository
        self._store_repository = store_repository

    def execute(self, dto: UpdateCategoryImageDTO) -> CategoryImage:
        self._get_owned_category(dto.store_id, dto.category_id, dto.owner_id)
        image = self._category_repository.get_image(dto.image_id)
        if image is None or image.category_id != dto.category_id:
            raise CategoryImageNotFoundError("Imagen no encontrada")

        if dto.is_primary is None and dto.image_file is None:
            raise DomainValidationError("No hay cambios para aplicar a la imagen")

        return self._category_repository.update_image(
            dto.image_id,
            is_primary=dto.is_primary,
            image_file=dto.image_file,
        )

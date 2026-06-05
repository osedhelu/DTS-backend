from features.products.application.dto import (
    CreateProductDTO,
    CreateServiceDTO,
    DeactivateProductDTO,
)
from features.products.domain.entities import Product, ProductType
from features.products.domain.exceptions import (
    CategoryNotFoundError,
    InvalidCategoryHierarchyError,
    ProductNotFoundError,
)
from features.products.domain.repositories import CategoryRepository, ProductRepository
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.domain.repositories import StoreRepository


class CreateProductUseCase:
    def __init__(
        self,
        product_repository: ProductRepository,
        category_repository: CategoryRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._product_repository = product_repository
        self._category_repository = category_repository
        self._store_repository = store_repository

    def execute(self, dto: CreateProductDTO) -> Product:
        self._ensure_store_owner(dto.store_id, dto.owner_id)
        self._validate_categories(
            store_id=dto.store_id,
            category_id=dto.category_id,
            subcategory_id=dto.subcategory_id,
        )

        product = Product(
            name=dto.name.strip(),
            price=dto.price,
            store_id=dto.store_id,
            stock=dto.stock,
            category_id=dto.category_id,
            subcategory_id=dto.subcategory_id,
            description=dto.description,
            product_type=ProductType.PHYSICAL,
        )

        return self._product_repository.create(
            {
                "name": product.name,
                "price": product.price,
                "store_id": product.store_id,
                "stock": product.stock,
                "category_id": product.category_id,
                "subcategory_id": product.subcategory_id,
                "description": product.description,
                "product_type": product.product_type,
                "requires_on_site_visit": product.requires_on_site_visit,
                "duration_minutes": product.duration_minutes,
                "is_active": product.is_active,
            }
        )

    def _ensure_store_owner(self, store_id: int, owner_id: int) -> None:
        store = self._store_repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {store_id} no encontrado")
        if store.owner_id != owner_id:
            raise NotStoreOwnerError("No tienes permiso para modificar este comercio")

    def _validate_categories(
        self,
        store_id: int,
        category_id: int | None,
        subcategory_id: int | None,
    ) -> None:
        if category_id is not None:
            category = self._category_repository.get_by_id(category_id)
            if category is None or category.store_id != store_id:
                raise CategoryNotFoundError(f"Categoría {category_id} no encontrada")
            if category.is_subcategory:
                raise InvalidCategoryHierarchyError(
                    "category_id debe ser una categoría raíz"
                )

        if subcategory_id is not None:
            subcategory = self._category_repository.get_by_id(subcategory_id)
            if subcategory is None or subcategory.store_id != store_id:
                raise CategoryNotFoundError(f"Subcategoría {subcategory_id} no encontrada")
            if not subcategory.is_subcategory:
                raise InvalidCategoryHierarchyError(
                    "subcategory_id debe ser una subcategoría"
                )
            if category_id is not None and subcategory.parent_id != category_id:
                raise InvalidCategoryHierarchyError(
                    "La subcategoría no pertenece a la categoría indicada"
                )


class CreateServiceUseCase(CreateProductUseCase):
    def execute(self, dto: CreateServiceDTO) -> Product:
        self._ensure_store_owner(dto.store_id, dto.owner_id)
        self._validate_categories(
            store_id=dto.store_id,
            category_id=dto.category_id,
            subcategory_id=dto.subcategory_id,
        )

        product = Product(
            name=dto.name.strip(),
            price=dto.price,
            store_id=dto.store_id,
            category_id=dto.category_id,
            subcategory_id=dto.subcategory_id,
            description=dto.description,
            product_type=ProductType.SERVICE,
            duration_minutes=dto.duration_minutes,
        )

        return self._product_repository.create(
            {
                "name": product.name,
                "price": product.price,
                "store_id": product.store_id,
                "stock": 0,
                "category_id": product.category_id,
                "subcategory_id": product.subcategory_id,
                "description": product.description,
                "product_type": product.product_type,
                "requires_on_site_visit": product.requires_on_site_visit,
                "duration_minutes": product.duration_minutes,
                "is_active": product.is_active,
            }
        )


class DeactivateProductUseCase:
    def __init__(
        self,
        product_repository: ProductRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._product_repository = product_repository
        self._store_repository = store_repository

    def execute(self, dto: DeactivateProductDTO) -> Product:
        product = self._product_repository.get_by_id(dto.product_id)
        if product is None:
            raise ProductNotFoundError(f"Producto {dto.product_id} no encontrado")

        store = self._store_repository.get_by_id(product.store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {product.store_id} no encontrado")
        if store.owner_id != dto.owner_id:
            raise NotStoreOwnerError("No tienes permiso para modificar este producto")

        return self._product_repository.deactivate(dto.product_id)

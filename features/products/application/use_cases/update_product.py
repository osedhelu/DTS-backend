from features.products.application.dto import (
    ReplaceIngredientsDTO,
    ReplaceVariantsDTO,
    UpdateProductDTO,
    UploadProductImageDTO,
)
from features.products.application.dynamic_field_validation import (
    validate_product_dynamic_values,
)
from features.products.domain.catalog_rules import assert_variants_allowed
from features.products.domain.entities import (
    Product,
    ProductDetails,
    ProductImage,
    ProductIngredient,
    ProductType,
    ProductVariant,
)
from features.products.domain.exceptions import (
    CategoryNotFoundError,
    DomainValidationError,
    InvalidCategoryHierarchyError,
    InvalidProductPriceError,
    ProductNotFoundError,
)
from features.products.domain.repositories import CategoryRepository, ProductRepository
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.domain.repositories import StoreRepository


class _ProductOwnershipMixin:
    _product_repository: ProductRepository
    _store_repository: StoreRepository

    def _get_owned_product(self, product_id: int, owner_id: int) -> Product:
        product = self._product_repository.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(f"Producto {product_id} no encontrado")

        store = self._store_repository.get_by_id(product.store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {product.store_id} no encontrado")
        if store.owner_id != owner_id:
            raise NotStoreOwnerError("No tienes permiso para modificar este producto")
        return product


class UpdateProductUseCase(_ProductOwnershipMixin):
    def __init__(
        self,
        product_repository: ProductRepository,
        category_repository: CategoryRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._product_repository = product_repository
        self._category_repository = category_repository
        self._store_repository = store_repository

    def execute(self, dto: UpdateProductDTO) -> ProductDetails:
        product = self._get_owned_product(dto.product_id, dto.owner_id)
        store = self._store_repository.get_by_id(product.store_id)
        assert store is not None

        if dto.variants is not None:
            assert_variants_allowed(
                product_type=product.product_type,
                store_vertical=store.vertical,
                has_variants=bool(dto.variants),
            )
            for variant in dto.variants:
                ProductVariant(
                    name=variant.name,
                    price=variant.price,
                    sort_order=variant.sort_order,
                )

        if dto.ingredients is not None:
            for ingredient in dto.ingredients:
                ProductIngredient(name=ingredient.name, is_allergen=ingredient.is_allergen)

        self._validate_categories(
            store_id=product.store_id,
            category_id=dto.category_id,
            subcategory_id=dto.subcategory_id,
        )

        update_data: dict = {}
        if dto.name is not None:
            update_data["name"] = dto.name.strip()
        if dto.price is not None:
            if dto.price <= 0:
                raise InvalidProductPriceError(
                    f"El precio debe ser positivo, recibido: {dto.price}"
                )
            update_data["price"] = dto.price
        if dto.description is not None:
            update_data["description"] = dto.description
        if dto.stock is not None:
            if not product.tracks_stock:
                raise DomainValidationError("Los servicios no gestionan inventario")
            update_data["stock"] = dto.stock
        if dto.category_id is not None:
            update_data["category_id"] = dto.category_id
        if dto.subcategory_id is not None:
            update_data["subcategory_id"] = dto.subcategory_id
        if dto.duration_minutes is not None:
            if product.product_type != ProductType.SERVICE:
                raise DomainValidationError("duration_minutes solo aplica a servicios")
            update_data["duration_minutes"] = dto.duration_minutes

        next_category_id = (
            dto.category_id if dto.category_id is not None else product.category_id
        )
        next_subcategory_id = (
            dto.subcategory_id
            if dto.subcategory_id is not None
            else product.subcategory_id
        )
        if (
            dto.dynamic_values is not None
            or dto.category_id is not None
            or dto.subcategory_id is not None
        ):
            raw_values = (
                dto.dynamic_values
                if dto.dynamic_values is not None
                else (product.dynamic_values or {})
            )
            update_data["dynamic_values"] = validate_product_dynamic_values(
                self._category_repository,
                store_id=product.store_id,
                category_id=next_category_id,
                subcategory_id=next_subcategory_id,
                raw_values=raw_values,
            )

        updated = (
            self._product_repository.update(dto.product_id, update_data)
            if update_data
            else product
        )

        variants = (
            self._product_repository.replace_variants(
                dto.product_id,
                [
                    {
                        "name": variant.name.strip(),
                        "price": variant.price,
                        "sort_order": variant.sort_order,
                    }
                    for variant in dto.variants
                ],
            )
            if dto.variants is not None
            else self._product_repository.list_variants(dto.product_id)
        )

        ingredients = (
            self._product_repository.replace_ingredients(
                dto.product_id,
                [
                    {
                        "name": ingredient.name.strip(),
                        "is_allergen": ingredient.is_allergen,
                    }
                    for ingredient in dto.ingredients
                ],
            )
            if dto.ingredients is not None
            else self._product_repository.list_ingredients(dto.product_id)
        )

        images = self._product_repository.list_images(dto.product_id)
        return ProductDetails(
            product=updated,
            variants=variants,
            ingredients=ingredients,
            images=images,
        )

    def _validate_categories(
        self,
        store_id: int,
        category_id: int | None,
        subcategory_id: int | None,
    ) -> None:
        if category_id is None and subcategory_id is None:
            return

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


class ReplaceVariantsUseCase(_ProductOwnershipMixin):
    def __init__(
        self,
        product_repository: ProductRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._product_repository = product_repository
        self._store_repository = store_repository

    def execute(self, dto: ReplaceVariantsDTO) -> list[ProductVariant]:
        product = self._get_owned_product(dto.product_id, dto.owner_id)
        store = self._store_repository.get_by_id(product.store_id)
        assert store is not None

        assert_variants_allowed(
            product_type=product.product_type,
            store_vertical=store.vertical,
            has_variants=bool(dto.variants),
        )

        for variant in dto.variants:
            ProductVariant(
                name=variant.name,
                price=variant.price,
                sort_order=variant.sort_order,
            )

        return self._product_repository.replace_variants(
            dto.product_id,
            [
                {
                    "name": variant.name.strip(),
                    "price": variant.price,
                    "sort_order": variant.sort_order,
                }
                for variant in dto.variants
            ],
        )


class ReplaceIngredientsUseCase(_ProductOwnershipMixin):
    def __init__(
        self,
        product_repository: ProductRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._product_repository = product_repository
        self._store_repository = store_repository

    def execute(self, dto: ReplaceIngredientsDTO) -> list[ProductIngredient]:
        self._get_owned_product(dto.product_id, dto.owner_id)

        for ingredient in dto.ingredients:
            ProductIngredient(name=ingredient.name, is_allergen=ingredient.is_allergen)

        return self._product_repository.replace_ingredients(
            dto.product_id,
            [
                {
                    "name": ingredient.name.strip(),
                    "is_allergen": ingredient.is_allergen,
                }
                for ingredient in dto.ingredients
            ],
        )


class UploadProductImageUseCase(_ProductOwnershipMixin):
    def __init__(
        self,
        product_repository: ProductRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._product_repository = product_repository
        self._store_repository = store_repository

    def execute(self, dto: UploadProductImageDTO) -> ProductImage:
        self._get_owned_product(dto.product_id, dto.owner_id)
        return self._product_repository.add_image(
            dto.product_id,
            dto.image_file,
            is_primary=dto.is_primary,
        )

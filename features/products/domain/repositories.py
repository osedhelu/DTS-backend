from typing import Any, Protocol

from features.products.domain.entities import (
    Category,
    Product,
    ProductImage,
    ProductIngredient,
    ProductType,
    ProductVariant,
)


class ProductRepository(Protocol):
    def create(self, data: dict[str, Any]) -> Product: ...

    def get_by_id(self, product_id: int) -> Product | None: ...

    def deactivate(self, product_id: int) -> Product: ...

    def update_stock(self, product_id: int, stock: int) -> Product: ...

    def update(self, product_id: int, data: dict[str, Any]) -> Product: ...

    def list_variants(self, product_id: int) -> list[ProductVariant]: ...

    def replace_variants(self, product_id: int, variants: list[dict[str, Any]]) -> list[ProductVariant]: ...

    def list_ingredients(self, product_id: int) -> list[ProductIngredient]: ...

    def replace_ingredients(
        self, product_id: int, ingredients: list[dict[str, Any]]
    ) -> list[ProductIngredient]: ...

    def list_images(self, product_id: int) -> list[ProductImage]: ...

    def add_image(
        self, product_id: int, image_file: Any, *, is_primary: bool = False
    ) -> ProductImage: ...

    def list_by_store(
        self,
        store_id: int,
        *,
        product_type: ProductType | None = None,
        category_id: int | None = None,
        subcategory_id: int | None = None,
        active_only: bool = True,
    ) -> list[Product]: ...


class CategoryRepository(Protocol):
    def create(self, data: dict[str, Any]) -> Category: ...

    def get_by_id(self, category_id: int) -> Category | None: ...

    def list_tree_by_store(self, store_id: int) -> list[dict[str, Any]]: ...

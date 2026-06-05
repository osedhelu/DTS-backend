from typing import Any, Protocol

from features.products.domain.entities import Category, Product, ProductType


class ProductRepository(Protocol):
    def create(self, data: dict[str, Any]) -> Product: ...

    def get_by_id(self, product_id: int) -> Product | None: ...

    def deactivate(self, product_id: int) -> Product: ...

    def update_stock(self, product_id: int, stock: int) -> Product: ...

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

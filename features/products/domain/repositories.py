from typing import Any, Protocol

from features.products.domain.entities import Category, Product


class ProductRepository(Protocol):
    def create(self, data: dict[str, Any]) -> Product: ...

    def get_by_id(self, product_id: int) -> Product | None: ...

    def deactivate(self, product_id: int) -> Product: ...


class CategoryRepository(Protocol):
    def create(self, data: dict[str, Any]) -> Category: ...

    def get_by_id(self, category_id: int) -> Category | None: ...

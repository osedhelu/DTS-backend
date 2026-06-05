from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CreateProductDTO:
    store_id: int
    owner_id: int
    name: str
    price: Decimal
    stock: int = 0
    category_id: int | None = None
    subcategory_id: int | None = None
    description: str = ""


@dataclass(frozen=True)
class CreateServiceDTO:
    store_id: int
    owner_id: int
    name: str
    price: Decimal
    category_id: int | None = None
    subcategory_id: int | None = None
    description: str = ""
    duration_minutes: int | None = None


@dataclass(frozen=True)
class DeactivateProductDTO:
    product_id: int
    owner_id: int


@dataclass(frozen=True)
class UpdateProductStockDTO:
    product_id: int
    owner_id: int
    stock: int


@dataclass(frozen=True)
class CreateCategoryDTO:
    store_id: int
    owner_id: int
    name: str


@dataclass(frozen=True)
class CreateSubcategoryDTO:
    store_id: int
    owner_id: int
    parent_id: int
    name: str

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
class ProductVariantInput:
    name: str
    price: Decimal
    sort_order: int = 0


@dataclass(frozen=True)
class ProductIngredientInput:
    name: str
    is_allergen: bool = False


@dataclass(frozen=True)
class UpdateProductDTO:
    product_id: int
    owner_id: int
    name: str | None = None
    price: Decimal | None = None
    description: str | None = None
    stock: int | None = None
    category_id: int | None = None
    subcategory_id: int | None = None
    duration_minutes: int | None = None
    variants: list[ProductVariantInput] | None = None
    ingredients: list[ProductIngredientInput] | None = None


@dataclass(frozen=True)
class ReplaceVariantsDTO:
    product_id: int
    owner_id: int
    variants: list[ProductVariantInput]


@dataclass(frozen=True)
class ReplaceIngredientsDTO:
    product_id: int
    owner_id: int
    ingredients: list[ProductIngredientInput]


@dataclass(frozen=True)
class UploadProductImageDTO:
    product_id: int
    owner_id: int
    image_file: object
    is_primary: bool = False


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

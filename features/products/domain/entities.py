from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from features.products.domain.exceptions import (
    InvalidIngredientError,
    InvalidProductPriceError,
    InvalidVariantError,
)


class ProductType(StrEnum):
    """Tipo de ítem en catálogo: producto tangible o servicio."""

    PHYSICAL = "physical"
    SERVICE = "service"


@dataclass
class Category:
    """
    Categoría de catálogo por tienda.

    Jerarquía de dos niveles: categoría raíz (parent_id=None) y subcategoría
    (parent_id apunta a la categoría padre).

    Ejemplos:
    - Comida → Hamburguesas, Bebidas
    - Servicios del hogar → Limpieza, Plomería
    """

    name: str
    store_id: int
    parent_id: int | None = None
    field_config: dict[str, list[str] | str] | None = None
    id: int | None = None

    @property
    def is_root(self) -> bool:
        return self.parent_id is None

    @property
    def is_subcategory(self) -> bool:
        return self.parent_id is not None


@dataclass
class Product:
    """
    Producto o servicio ofrecido por una tienda.

    PHYSICAL: comida, bebidas, artículos con inventario (stock).
    SERVICE: limpieza a domicilio, reparaciones, etc. — sin stock;
    puede requerir visita al cliente y duración estimada.
    """

    name: str
    price: Decimal
    store_id: int
    product_type: ProductType = ProductType.PHYSICAL
    category_id: int | None = None
    subcategory_id: int | None = None
    stock: int = 0
    description: str = ""
    is_active: bool = True
    requires_on_site_visit: bool = False
    duration_minutes: int | None = None
    dynamic_values: dict[str, str] | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise InvalidProductPriceError(
                f"El precio debe ser positivo, recibido: {self.price}"
            )
        if self.product_type == ProductType.SERVICE:
            self.requires_on_site_visit = True
        elif self.requires_on_site_visit:
            self.requires_on_site_visit = False

    @property
    def tracks_stock(self) -> bool:
        return self.product_type == ProductType.PHYSICAL

    @property
    def is_service(self) -> bool:
        return self.product_type == ProductType.SERVICE


@dataclass
class ProductVariant:
    """Porción o tamaño con precio propio (ej. S/M/L/XL)."""

    name: str
    price: Decimal
    sort_order: int = 0
    id: int | None = None
    product_id: int | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidVariantError("El nombre de la variante es obligatorio")
        if self.price <= 0:
            raise InvalidProductPriceError(
                f"El precio de variante debe ser positivo, recibido: {self.price}"
            )


@dataclass
class ProductIngredient:
    name: str
    is_allergen: bool = False
    id: int | None = None
    product_id: int | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidIngredientError("El nombre del ingrediente es obligatorio")


@dataclass
class ProductImage:
    product_id: int
    image_path: str
    is_primary: bool = False
    id: int | None = None


@dataclass
class ProductDetails:
    product: Product
    variants: list[ProductVariant]
    ingredients: list[ProductIngredient]
    images: list[ProductImage]

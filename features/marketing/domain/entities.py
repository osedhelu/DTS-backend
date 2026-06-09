from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from features.marketing.domain.exceptions import InvalidCouponError, InvalidStorePromotionError


class DiscountType(StrEnum):
    PERCENTAGE = "PERCENTAGE"
    FIXED = "FIXED"


@dataclass
class Coupon:
    code: str
    discount_type: DiscountType
    discount_value: Decimal
    min_order_total: Decimal = Decimal("0")
    max_uses: int | None = None
    used_count: int = 0
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        if self.discount_value <= 0:
            raise InvalidCouponError("El valor de descuento debe ser positivo")
        if self.discount_type == DiscountType.PERCENTAGE and self.discount_value > 100:
            raise InvalidCouponError("El descuento porcentual no puede superar 100")
        if self.min_order_total < 0:
            raise InvalidCouponError("El mínimo de pedido no puede ser negativo")
        if self.max_uses is not None and self.max_uses <= 0:
            raise InvalidCouponError("max_uses debe ser positivo cuando está definido")
        if self.used_count < 0:
            raise InvalidCouponError("used_count no puede ser negativo")
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_until < self.valid_from
        ):
            raise InvalidCouponError("valid_until debe ser posterior a valid_from")


@dataclass
class Banner:
    title: str
    image_url: str
    link_url: str = ""
    is_active: bool = True
    sort_order: int = 0
    id: int | None = None


@dataclass
class StorePromotion:
    store_id: int
    name: str
    discount_type: DiscountType
    discount_value: Decimal
    product_id: int | None = None
    variant_id: int | None = None
    param_key: str | None = None
    param_value: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidStorePromotionError("El nombre de la promoción es obligatorio")
        if self.discount_value <= 0:
            raise InvalidStorePromotionError("El valor de descuento debe ser positivo")
        if self.discount_type == DiscountType.PERCENTAGE and self.discount_value > 100:
            raise InvalidStorePromotionError("El descuento porcentual no puede superar 100")
        if self.variant_id is not None and self.product_id is None:
            raise InvalidStorePromotionError(
                "variant_id requiere un product_id asociado"
            )
        if self.param_value is not None and not self.param_key:
            raise InvalidStorePromotionError(
                "param_value requiere param_key"
            )
        if self.param_key is not None and self.product_id is None:
            raise InvalidStorePromotionError(
                "param_key requiere un product_id asociado"
            )
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_until < self.valid_from
        ):
            raise InvalidStorePromotionError("valid_until debe ser posterior a valid_from")

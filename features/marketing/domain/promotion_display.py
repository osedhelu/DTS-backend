from datetime import datetime
from decimal import Decimal

from features.marketing.domain.entities import DiscountType, StorePromotion


def promotion_is_currently_active(
    promotion: StorePromotion,
    *,
    now: datetime | None = None,
) -> bool:
    if not promotion.is_active:
        return False

    current_time = now or datetime.now(
        tz=promotion.valid_from.tzinfo if promotion.valid_from else None
    )

    if promotion.valid_from is not None and current_time < promotion.valid_from:
        return False

    if promotion.valid_until is not None and current_time > promotion.valid_until:
        return False

    return True


def format_discount_badge(
    promotion: StorePromotion,
    *,
    option_label: str | None = None,
) -> str:
    if promotion.discount_type == DiscountType.PERCENTAGE:
        value = promotion.discount_value.quantize(Decimal("0.01"))
        normalized = value.to_integral() if value == value.to_integral() else value
        badge = f"-{normalized}%"
    else:
        badge = f"-${promotion.discount_value.quantize(Decimal('0.01'))}"

    label = option_label or promotion.param_value
    if label:
        return f"{badge} · {label}"

    return badge


def promotion_specificity(promotion: StorePromotion) -> int:
    if promotion.param_key and promotion.param_value:
        return 4
    if promotion.variant_id is not None:
        return 3
    if promotion.product_id is not None:
        return 2
    return 1

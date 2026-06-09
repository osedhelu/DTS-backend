from datetime import datetime, timezone
from decimal import Decimal

import pytest

from features.marketing.domain.entities import DiscountType, StorePromotion
from features.marketing.domain.exceptions import (
    InvalidStorePromotionError,
    StorePromotionNotApplicableError,
)
from features.marketing.domain.promotion_display import format_discount_badge
from features.marketing.domain.services import StorePromotionDiscountCalculator


def test_store_promotion_discount_calculation_variant_specific():
    promotion = StorePromotion(
        store_id=1,
        name="Promo talla XL",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("20"),
        product_id=42,
        variant_id=7,
    )

    with pytest.raises(StorePromotionNotApplicableError, match="variante"):
        StorePromotionDiscountCalculator.calculate(
            Decimal("30000.00"),
            promotion,
            product_id=42,
            variant_id=8,
        )

    discount = StorePromotionDiscountCalculator.calculate(
        Decimal("30000.00"),
        promotion,
        product_id=42,
        variant_id=7,
    )
    assert discount == Decimal("6000.00")


def test_format_discount_badge_with_variant_name():
    promotion = StorePromotion(
        store_id=1,
        name="Promo XL",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("15"),
    )

    assert format_discount_badge(promotion, option_label="XL") == "-15% · XL"


def test_store_promotion_entity_requires_product_for_variant():
    with pytest.raises(InvalidStorePromotionError, match="variant_id requiere"):
        StorePromotion(
            store_id=1,
            name="Invalida",
            discount_type=DiscountType.FIXED,
            discount_value=Decimal("1000"),
            variant_id=5,
        )

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from features.marketing.domain.entities import DiscountType, StorePromotion
from features.marketing.domain.exceptions import (
    InvalidStorePromotionError,
    StorePromotionNotApplicableError,
)
from features.marketing.domain.services import StorePromotionDiscountCalculator


def test_store_promotion_discount_calculation_percentage():
    promotion = StorePromotion(
        store_id=1,
        name="Descuento 10%",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
    )

    discount = StorePromotionDiscountCalculator.calculate(
        Decimal("100000.00"),
        promotion,
    )

    assert discount == Decimal("10000.00")


def test_store_promotion_discount_calculation_fixed():
    promotion = StorePromotion(
        store_id=1,
        name="5000 off",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("5000.00"),
    )

    discount = StorePromotionDiscountCalculator.calculate(
        Decimal("50000.00"),
        promotion,
    )

    assert discount == Decimal("5000.00")


def test_store_promotion_discount_calculation_product_specific():
    promotion = StorePromotion(
        store_id=1,
        name="Promo hamburguesa",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("15"),
        product_id=42,
    )

    with pytest.raises(StorePromotionNotApplicableError, match="producto"):
        StorePromotionDiscountCalculator.calculate(
            Decimal("30000.00"),
            promotion,
            product_id=99,
        )

    discount = StorePromotionDiscountCalculator.calculate(
        Decimal("30000.00"),
        promotion,
        product_id=42,
    )
    assert discount == Decimal("4500.00")


def test_store_promotion_discount_calculation_rejects_expired():
    promotion = StorePromotion(
        store_id=1,
        name="Expirada",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("1000.00"),
        valid_until=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(StorePromotionNotApplicableError, match="expirado"):
        StorePromotionDiscountCalculator.calculate(
            Decimal("50000.00"),
            promotion,
            now=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )


def test_store_promotion_entity_rejects_invalid_percentage():
    with pytest.raises(InvalidStorePromotionError, match="100"):
        StorePromotion(
            store_id=1,
            name="Mala promo",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("150"),
        )

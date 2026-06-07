from datetime import datetime, timezone
from decimal import Decimal

import pytest

from features.marketing.domain.entities import Coupon, DiscountType
from features.marketing.domain.exceptions import CouponNotApplicableError, InvalidCouponError
from features.marketing.domain.services import CouponDiscountCalculator


def test_coupon_discount_calculation_percentage():
    coupon = Coupon(
        code="SAVE10",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
    )

    discount = CouponDiscountCalculator.calculate(Decimal("100000.00"), coupon)

    assert discount == Decimal("10000.00")


def test_coupon_discount_calculation_fixed():
    coupon = Coupon(
        code="FLAT5K",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("5000.00"),
    )

    discount = CouponDiscountCalculator.calculate(Decimal("50000.00"), coupon)

    assert discount == Decimal("5000.00")


def test_coupon_discount_calculation_fixed_capped_at_order_total():
    coupon = Coupon(
        code="BIGOFF",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("20000.00"),
    )

    discount = CouponDiscountCalculator.calculate(Decimal("15000.00"), coupon)

    assert discount == Decimal("15000.00")


def test_coupon_discount_calculation_rejects_inactive_coupon():
    coupon = Coupon(
        code="OFF",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("1000.00"),
        is_active=False,
    )

    with pytest.raises(CouponNotApplicableError, match="activo"):
        CouponDiscountCalculator.calculate(Decimal("50000.00"), coupon)


def test_coupon_discount_calculation_rejects_below_min_order_total():
    coupon = Coupon(
        code="MIN50K",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("15"),
        min_order_total=Decimal("50000.00"),
    )

    with pytest.raises(CouponNotApplicableError, match="mínimo"):
        CouponDiscountCalculator.calculate(Decimal("30000.00"), coupon)


def test_coupon_discount_calculation_rejects_expired_coupon():
    coupon = Coupon(
        code="EXPIRED",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("1000.00"),
        valid_until=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(CouponNotApplicableError, match="expirado"):
        CouponDiscountCalculator.calculate(
            Decimal("50000.00"),
            coupon,
            now=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )


def test_coupon_discount_calculation_rejects_max_uses_reached():
    coupon = Coupon(
        code="LIMITED",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("1000.00"),
        max_uses=10,
        used_count=10,
    )

    with pytest.raises(CouponNotApplicableError, match="límite"):
        CouponDiscountCalculator.calculate(Decimal("50000.00"), coupon)


def test_coupon_entity_rejects_invalid_percentage():
    with pytest.raises(InvalidCouponError, match="100"):
        Coupon(
            code="BAD",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("150"),
        )

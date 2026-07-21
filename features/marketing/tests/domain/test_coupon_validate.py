import pytest
from decimal import Decimal

from features.marketing.domain.entities import Coupon, DiscountType
from features.marketing.domain.services import CouponDiscountCalculator


def test_coupon_percentage_discount():
    coupon = Coupon(
        code="TEST10",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
        min_order_total=Decimal("0"),
        max_uses=None,
        used_count=0,
        valid_from=None,
        valid_until=None,
        is_active=True,
    )
    discount = CouponDiscountCalculator.calculate(Decimal("100"), coupon)
    assert discount == Decimal("10.00")

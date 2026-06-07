from datetime import datetime
from decimal import Decimal

from features.marketing.domain.entities import Coupon, DiscountType
from features.marketing.domain.exceptions import CouponNotApplicableError


class CouponDiscountCalculator:
    @staticmethod
    def calculate(
        order_total: Decimal,
        coupon: Coupon,
        *,
        now: datetime | None = None,
    ) -> Decimal:
        if order_total <= 0:
            raise CouponNotApplicableError("El total del pedido debe ser positivo")

        if not coupon.is_active:
            raise CouponNotApplicableError("El cupón no está activo")

        current_time = now or datetime.now(tz=coupon.valid_from.tzinfo if coupon.valid_from else None)

        if coupon.valid_from is not None and current_time < coupon.valid_from:
            raise CouponNotApplicableError("El cupón aún no es válido")

        if coupon.valid_until is not None and current_time > coupon.valid_until:
            raise CouponNotApplicableError("El cupón ha expirado")

        if order_total < coupon.min_order_total:
            raise CouponNotApplicableError(
                f"El pedido no alcanza el mínimo de {coupon.min_order_total}"
            )

        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
            raise CouponNotApplicableError("El cupón alcanzó el límite de usos")

        if coupon.discount_type == DiscountType.PERCENTAGE:
            discount = (order_total * coupon.discount_value / Decimal("100")).quantize(
                Decimal("0.01")
            )
        else:
            discount = coupon.discount_value.quantize(Decimal("0.01"))

        return min(discount, order_total)

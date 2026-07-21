"""Validación de cupones en checkout."""

from decimal import Decimal

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from features.marketing.domain.entities import Coupon
from features.marketing.domain.exceptions import CouponNotApplicableError
from features.marketing.domain.services import CouponDiscountCalculator
from features.marketing.infrastructure.models import CouponModel


class ValidateCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)
    order_total = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))


@extend_schema_view(
    post=extend_schema(request=ValidateCouponSerializer, responses={200: ValidateCouponSerializer}),
)
class ValidateCouponView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ValidateCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"].strip()
        order_total = serializer.validated_data["order_total"]

        model = CouponModel.objects.filter(code__iexact=code).first()
        if model is None:
            return Response({"detail": "Cupón no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        coupon = Coupon(
            code=model.code,
            discount_type=model.discount_type,
            discount_value=model.discount_value,
            min_order_total=model.min_order_total,
            max_uses=model.max_uses,
            used_count=model.used_count,
            valid_from=model.valid_from,
            valid_until=model.valid_until,
            is_active=model.is_active,
        )
        try:
            discount = CouponDiscountCalculator.calculate(order_total, coupon)
        except CouponNotApplicableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "code": model.code,
                "discount_amount": str(discount),
                "final_total": str(order_total - discount),
            }
        )

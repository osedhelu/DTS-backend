"""Pago simulado (sandbox DTS) para desarrollo y demos."""

from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsCustomer
from features.orders.infrastructure.models import Order
from features.stores.domain.dashboard_entities import DEFAULT_PLATFORM_COMMISSION_RATE


class SandboxPaySerializer(serializers.Serializer):
    card_last4 = serializers.CharField(max_length=4, required=False, default="4242")
    sandbox_reference = serializers.CharField(required=False, allow_blank=True, default="")


class SandboxReceiptSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    payment_status = serializers.CharField()
    payment_reference = serializers.CharField()
    paid_at = serializers.DateTimeField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    platform_commission_rate = serializers.DecimalField(max_digits=5, decimal_places=4)
    platform_commission = serializers.DecimalField(max_digits=12, decimal_places=2)
    merchant_net = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method_label = serializers.CharField()


@extend_schema_view(
    get=extend_schema(
        responses={
            200: inline_serializer(
                name="PaymentSandboxConfig",
                fields={"enabled": serializers.BooleanField()},
            )
        }
    ),
)
class PaymentSandboxConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"enabled": bool(getattr(settings, "PAYMENT_SANDBOX_ENABLED", False))})


def build_sandbox_receipt(order: Order) -> dict:
    subtotal = order.total + order.discount_amount
    commission_rate = DEFAULT_PLATFORM_COMMISSION_RATE
    commission = (order.total * commission_rate).quantize(Decimal("0.01"))
    merchant_net = (order.total - commission).quantize(Decimal("0.01"))
    return {
        "order_id": order.id,
        "payment_status": order.payment_status,
        "payment_reference": order.payment_reference,
        "paid_at": order.paid_at,
        "subtotal": subtotal,
        "discount_amount": order.discount_amount,
        "total_paid": order.total,
        "platform_commission_rate": commission_rate,
        "platform_commission": commission,
        "merchant_net": merchant_net,
        "payment_method_label": "Sandbox DTS",
    }


@extend_schema_view(
    post=extend_schema(
        request=SandboxPaySerializer,
        responses={200: SandboxReceiptSerializer, 400: DetailErrorSerializer, 403: DetailErrorSerializer},
    ),
)
class OrderSandboxPayView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request, order_id: int):
        if not getattr(settings, "PAYMENT_SANDBOX_ENABLED", False):
            return Response(
                {"detail": "Sandbox de pagos deshabilitado"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SandboxPaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        order = Order.objects.filter(pk=order_id, customer_id=request.user.id).first()
        if order is None:
            return Response({"detail": "Pedido no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if order.payment_status not in ("pending", "cash_on_delivery"):
            return Response(
                {"detail": "El pedido no está pendiente de pago"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        last4 = (data.get("card_last4") or "4242").strip()[-4:]
        reference = (data.get("sandbox_reference") or "").strip()
        if not reference:
            reference = f"sandbox:{order.id}:{last4}:{timezone.now().strftime('%Y%m%d%H%M%S')}"

        order.payment_status = "paid"
        order.payment_reference = reference
        order.paid_at = timezone.now()
        order.save(
            update_fields=["payment_status", "payment_reference", "paid_at", "updated_at"]
        )

        return Response(build_sandbox_receipt(order))

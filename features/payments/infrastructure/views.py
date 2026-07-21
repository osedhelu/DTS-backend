"""API de métodos de pago por tienda."""

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsMerchant
from features.orders.infrastructure.models import Order
from features.payments.infrastructure.models import StorePaymentMethod
from features.payments.infrastructure.serializers import (
    ConfirmPaymentSerializer,
    CreateStorePaymentMethodSerializer,
    UpdateStorePaymentMethodSerializer,
    serialize_payment_method,
)
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.infrastructure.models import Store


def _assert_store_owner(store_id: int, owner_id: int) -> Store:
    store = Store.objects.filter(pk=store_id).first()
    if store is None:
        raise StoreNotFoundError(f"Comercio {store_id} no encontrado")
    if store.owner_id != owner_id:
        raise NotStoreOwnerError("No eres dueño de este comercio")
    return store


@extend_schema_view(
    get=extend_schema(responses={200: CreateStorePaymentMethodSerializer(many=True)}),
    post=extend_schema(
        request=CreateStorePaymentMethodSerializer,
        responses={201: CreateStorePaymentMethodSerializer},
    ),
)
class StorePaymentMethodListView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsMerchant()]

    def get(self, request, store_id: int):
        methods = StorePaymentMethod.objects.filter(
            store_id=store_id, is_active=True
        ).order_by("sort_order", "name")
        payload = [serialize_payment_method(m) for m in methods]
        if getattr(settings, "PAYMENT_SANDBOX_ENABLED", False):
            payload.append(
                {
                    "id": 0,
                    "store_id": store_id,
                    "method_type": "sandbox",
                    "name": "Sandbox DTS (simulado)",
                    "instructions": "Pago de prueba — no se cobra dinero real.",
                    "qr_image_url": "",
                    "is_active": True,
                    "sort_order": 999,
                }
            )
        return Response(payload)

    def post(self, request, store_id: int):
        serializer = CreateStorePaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            _assert_store_owner(store_id, request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        method = StorePaymentMethod.objects.create(store_id=store_id, **data)
        return Response(serialize_payment_method(method), status=status.HTTP_201_CREATED)


@extend_schema_view(
    patch=extend_schema(
        request=UpdateStorePaymentMethodSerializer,
        responses={200: CreateStorePaymentMethodSerializer, 404: DetailErrorSerializer},
    ),
    delete=extend_schema(responses={204: None}),
)
class StorePaymentMethodDetailView(APIView):
    permission_classes = [IsMerchant]

    def patch(self, request, store_id: int, method_id: int):
        serializer = UpdateStorePaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            _assert_store_owner(store_id, request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        method = StorePaymentMethod.objects.filter(
            pk=method_id, store_id=store_id
        ).first()
        if method is None:
            return Response({"detail": "Método no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        for key, value in serializer.validated_data.items():
            setattr(method, key, value)
        method.save()
        return Response(serialize_payment_method(method))

    def delete(self, request, store_id: int, method_id: int):
        try:
            _assert_store_owner(store_id, request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        deleted, _ = StorePaymentMethod.objects.filter(
            pk=method_id, store_id=store_id
        ).delete()
        if not deleted:
            return Response({"detail": "Método no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    post=extend_schema(
        request=ConfirmPaymentSerializer,
        responses={200: ConfirmPaymentSerializer, 403: DetailErrorSerializer},
    ),
)
class OrderConfirmPaymentView(APIView):
    permission_classes = [IsMerchant]

    def post(self, request, order_id: int):
        serializer = ConfirmPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = Order.objects.select_related("store").filter(pk=order_id).first()
        if order is None:
            return Response({"detail": "Pedido no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        if order.store.owner_id != request.user.id:
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        order.payment_status = "paid"
        order.payment_reference = serializer.validated_data.get("payment_reference", "")
        order.paid_at = timezone.now()
        order.save(
            update_fields=[
                "payment_status",
                "payment_reference",
                "paid_at",
                "updated_at",
            ]
        )
        return Response(
            {
                "order_id": order.id,
                "payment_status": order.payment_status,
                "paid_at": order.paid_at,
            }
        )

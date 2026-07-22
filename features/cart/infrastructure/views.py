from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsCustomer
from features.cart.application.dto import UpdateCartItemQuantityDTO, UpsertCartItemDTO
from features.cart.application.use_cases.clear_cart import ClearCartUseCase
from features.cart.application.use_cases.get_cart import GetCartUseCase
from features.cart.application.use_cases.update_cart_item_quantity import (
    UpdateCartItemQuantityUseCase,
)
from features.cart.application.use_cases.upsert_cart_item import UpsertCartItemUseCase
from features.cart.domain.exceptions import (
    CartItemNotFoundError,
    CartProductNotFoundError,
    CartStoreConflictError,
)
from features.cart.infrastructure.serializers import (
    CartItemQuantitySerializer,
    CartItemUpsertSerializer,
    CartResponseSerializer,
)
from features.cart.infrastructure.serializers_helpers import serialize_cart


@extend_schema_view(
    get=extend_schema(responses={200: CartResponseSerializer}),
    delete=extend_schema(responses={204: None}),
)
class CartDetailView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        cart = GetCartUseCase().execute(request.user.id)
        return Response(serialize_cart(cart))

    def delete(self, request):
        ClearCartUseCase().execute(request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    post=extend_schema(
        request=CartItemUpsertSerializer,
        responses={
            200: CartResponseSerializer,
            400: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class CartItemsView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = CartItemUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            cart = UpsertCartItemUseCase().execute(
                UpsertCartItemDTO(
                    customer_id=request.user.id,
                    product_id=data["product_id"],
                    quantity=data["quantity"],
                    notes=data.get("notes") or "",
                    replace_store=data.get("replace_store", True),
                )
            )
        except CartProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except CartStoreConflictError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        cart = GetCartUseCase().execute(request.user.id) or cart
        return Response(serialize_cart(cart))


@extend_schema_view(
    patch=extend_schema(
        request=CartItemQuantitySerializer,
        responses={
            200: CartResponseSerializer,
            404: DetailErrorSerializer,
        },
    ),
    delete=extend_schema(responses={200: CartResponseSerializer, 404: DetailErrorSerializer}),
)
class CartItemDetailView(APIView):
    permission_classes = [IsCustomer]

    def patch(self, request, product_id: int):
        serializer = CartItemQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            UpdateCartItemQuantityUseCase().execute(
                UpdateCartItemQuantityDTO(
                    customer_id=request.user.id,
                    product_id=product_id,
                    quantity=serializer.validated_data["quantity"],
                )
            )
        except CartItemNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        cart = GetCartUseCase().execute(request.user.id)
        return Response(serialize_cart(cart))

    def delete(self, request, product_id: int):
        try:
            UpdateCartItemQuantityUseCase().execute(
                UpdateCartItemQuantityDTO(
                    customer_id=request.user.id,
                    product_id=product_id,
                    quantity=0,
                )
            )
        except CartItemNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        cart = GetCartUseCase().execute(request.user.id)
        return Response(serialize_cart(cart))

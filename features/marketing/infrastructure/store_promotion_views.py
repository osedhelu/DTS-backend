from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.pagination import paginate_list
from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsMerchant
from features.marketing.application.use_cases.manage_store_promotion import (
    CreateStorePromotionDTO,
    CreateStorePromotionUseCase,
    DeactivateStorePromotionDTO,
    DeactivateStorePromotionUseCase,
    ListStorePromotionsUseCase,
    UNSET,
    UpdateStorePromotionDTO,
    UpdateStorePromotionUseCase,
)
from features.marketing.domain.entities import DiscountType
from features.marketing.domain.exceptions import (
    InvalidStorePromotionError,
    StorePromotionNotFoundError,
)
from features.products.domain.exceptions import ProductNotFoundError
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.marketing.infrastructure.store_promotion_serializers import (
    CreateStorePromotionSerializer,
    StorePromotionSerializer,
    UpdateStorePromotionSerializer,
)


def _promotion_repository_bundle():
    from features.marketing.infrastructure.repositories import DjangoStorePromotionRepository
    from features.products.infrastructure.repositories import DjangoProductRepository
    from features.stores.infrastructure.repositories import DjangoStoreRepository

    return (
        DjangoStorePromotionRepository(),
        DjangoStoreRepository(),
        DjangoProductRepository(),
    )


@extend_schema_view(
    get=extend_schema(responses={200: StorePromotionSerializer(many=True)}),
    post=extend_schema(
        request=CreateStorePromotionSerializer,
        responses={201: StorePromotionSerializer, 400: DetailErrorSerializer},
    ),
)
class StorePromotionListCreateView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request, store_id: int):
        promotion_repository, store_repository, product_repository = _promotion_repository_bundle()

        try:
            promotions = ListStorePromotionsUseCase(
                promotion_repository,
                store_repository,
                product_repository,
            ).execute(store_id=store_id, owner_id=request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return paginate_list(
            request,
            promotions,
            lambda page: StorePromotionSerializer(page, many=True).data,
        )

    def post(self, request, store_id: int):
        promotion_repository, store_repository, product_repository = _promotion_repository_bundle()

        serializer = CreateStorePromotionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            promotion = CreateStorePromotionUseCase(
                promotion_repository,
                store_repository,
                product_repository,
            ).execute(
                CreateStorePromotionDTO(
                    store_id=store_id,
                    owner_id=request.user.id,
                    name=data["name"],
                    discount_type=DiscountType(data["discount_type"]),
                    discount_value=data["discount_value"],
                    product_id=data.get("product_id"),
                    variant_id=data.get("variant_id"),
                    param_key=data.get("param_key"),
                    param_value=data.get("param_value"),
                    valid_from=data.get("valid_from"),
                    valid_until=data.get("valid_until"),
                )
            )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidStorePromotionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StorePromotionSerializer(promotion).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    patch=extend_schema(
        request=UpdateStorePromotionSerializer,
        responses={200: StorePromotionSerializer, 400: DetailErrorSerializer},
    ),
)
class StorePromotionDetailView(APIView):
    permission_classes = [IsMerchant]

    def patch(self, request, store_id: int, promotion_id: int):
        promotion_repository, store_repository, product_repository = _promotion_repository_bundle()

        serializer = UpdateStorePromotionSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            if data.get("is_active") is False and len(data) == 1:
                promotion = DeactivateStorePromotionUseCase(
                    promotion_repository,
                    store_repository,
                    product_repository,
                ).execute(
                    DeactivateStorePromotionDTO(
                        promotion_id=promotion_id,
                        store_id=store_id,
                        owner_id=request.user.id,
                    )
                )
            else:
                promotion = UpdateStorePromotionUseCase(
                    promotion_repository,
                    store_repository,
                    product_repository,
                ).execute(
                    UpdateStorePromotionDTO(
                        promotion_id=promotion_id,
                        store_id=store_id,
                        owner_id=request.user.id,
                        name=data.get("name"),
                        discount_type=(
                            DiscountType(data["discount_type"])
                            if "discount_type" in data
                            else None
                        ),
                        discount_value=data.get("discount_value"),
                        product_id=data.get("product_id"),
                        variant_id=data.get("variant_id"),
                        param_key=data.get("param_key"),
                        param_value=data.get("param_value"),
                        valid_from=(
                            data["valid_from"] if "valid_from" in data else UNSET
                        ),
                        valid_until=(
                            data["valid_until"] if "valid_until" in data else UNSET
                        ),
                        is_active=data.get("is_active"),
                    )
                )
        except StorePromotionNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidStorePromotionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StorePromotionSerializer(promotion).data)

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsMerchant
from features.products.application.dto import (
    DeleteProductImageDTO,
    ReplaceIngredientsDTO,
    ReplaceVariantsDTO,
    UpdateProductImageDTO,
    UploadProductImageDTO,
)
from features.products.domain.exceptions import (
    DomainValidationError,
    ProductNotFoundError,
    ProductImageNotFoundError,
    VariantsNotAllowedError,
)
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.products.infrastructure.serializers import (
    ProductImageSerializer,
    ProductIngredientSerializer,
    ProductVariantSerializer,
    ReplaceIngredientsSerializer,
    ReplaceVariantsSerializer,
    UpdateProductImageSerializer,
    UploadProductImageSerializer,
)


@extend_schema_view(
    get=extend_schema(responses={200: ProductVariantSerializer(many=True)}),
    put=extend_schema(
        request=ReplaceVariantsSerializer,
        responses={200: ProductVariantSerializer(many=True), 400: DetailErrorSerializer},
    ),
)
class ProductVariantListView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request, store_id: int, product_id: int):
        from features.products.infrastructure.repositories import DjangoProductRepository

        repository = DjangoProductRepository()
        product = repository.get_by_id(product_id)
        if product is None or product.store_id != store_id:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        variants = repository.list_variants(product_id)
        return Response(ProductVariantSerializer(variants, many=True).data)

    def put(self, request, store_id: int, product_id: int):
        from features.products.application.dto import ProductVariantInput
        from features.products.application.use_cases.update_product import ReplaceVariantsUseCase
        from features.products.infrastructure.repositories import (
            DjangoProductRepository,
        )
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = ReplaceVariantsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            variants = ReplaceVariantsUseCase(
                DjangoProductRepository(),
                DjangoStoreRepository(),
            ).execute(
                ReplaceVariantsDTO(
                    product_id=product_id,
                    owner_id=request.user.id,
                    variants=[
                        ProductVariantInput(
                            name=item["name"],
                            price=item["price"],
                            sort_order=item.get("sort_order", 0),
                        )
                        for item in serializer.validated_data["variants"]
                    ],
                )
            )
        except ProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (StoreNotFoundError, NotStoreOwnerError) as exc:
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(exc, NotStoreOwnerError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response({"detail": str(exc)}, status=status_code)
        except (VariantsNotAllowedError, DomainValidationError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        product = DjangoProductRepository().get_by_id(product_id)
        if product is None or product.store_id != store_id:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(ProductVariantSerializer(variants, many=True).data)


@extend_schema_view(
    get=extend_schema(responses={200: ProductIngredientSerializer(many=True)}),
    put=extend_schema(
        request=ReplaceIngredientsSerializer,
        responses={200: ProductIngredientSerializer(many=True), 400: DetailErrorSerializer},
    ),
)
class ProductIngredientListView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request, store_id: int, product_id: int):
        from features.products.infrastructure.repositories import DjangoProductRepository

        repository = DjangoProductRepository()
        product = repository.get_by_id(product_id)
        if product is None or product.store_id != store_id:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        ingredients = repository.list_ingredients(product_id)
        return Response(ProductIngredientSerializer(ingredients, many=True).data)

    def put(self, request, store_id: int, product_id: int):
        from features.products.application.dto import ProductIngredientInput
        from features.products.application.use_cases.update_product import (
            ReplaceIngredientsUseCase,
        )
        from features.products.infrastructure.repositories import DjangoProductRepository
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = ReplaceIngredientsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ingredients = ReplaceIngredientsUseCase(
                DjangoProductRepository(),
                DjangoStoreRepository(),
            ).execute(
                ReplaceIngredientsDTO(
                    product_id=product_id,
                    owner_id=request.user.id,
                    ingredients=[
                        ProductIngredientInput(
                            name=item["name"],
                            is_allergen=item.get("is_allergen", False),
                        )
                        for item in serializer.validated_data["ingredients"]
                    ],
                )
            )
        except ProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (StoreNotFoundError, NotStoreOwnerError) as exc:
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(exc, NotStoreOwnerError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response({"detail": str(exc)}, status=status_code)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        product = DjangoProductRepository().get_by_id(product_id)
        if product is None or product.store_id != store_id:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(ProductIngredientSerializer(ingredients, many=True).data)


@extend_schema_view(
    get=extend_schema(responses={200: ProductImageSerializer(many=True)}),
    post=extend_schema(
        request=UploadProductImageSerializer,
        responses={201: ProductImageSerializer, 400: DetailErrorSerializer},
    ),
)
class ProductImageUploadView(APIView):
    permission_classes = [IsMerchant]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, store_id: int, product_id: int):
        from features.products.infrastructure.repositories import DjangoProductRepository

        repository = DjangoProductRepository()
        product = repository.get_by_id(product_id)
        if product is None or product.store_id != store_id:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        images = repository.list_images(product_id)
        return Response(
            [
                {
                    "id": image.id,
                    "url": image.image_path,
                    "is_primary": image.is_primary,
                }
                for image in images
            ]
        )

    def post(self, request, store_id: int, product_id: int):
        from features.products.application.use_cases.update_product import (
            UploadProductImageUseCase,
        )
        from features.products.infrastructure.repositories import DjangoProductRepository
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = UploadProductImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            image = UploadProductImageUseCase(
                DjangoProductRepository(),
                DjangoStoreRepository(),
            ).execute(
                UploadProductImageDTO(
                    product_id=product_id,
                    owner_id=request.user.id,
                    image_file=serializer.validated_data["image"],
                    is_primary=serializer.validated_data.get("is_primary", False),
                )
            )
        except ProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (StoreNotFoundError, NotStoreOwnerError) as exc:
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(exc, NotStoreOwnerError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response({"detail": str(exc)}, status=status_code)

        product = DjangoProductRepository().get_by_id(product_id)
        if product is None or product.store_id != store_id:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "id": image.id,
                "url": image.image_path,
                "is_primary": image.is_primary,
            },
            status=status.HTTP_201_CREATED,
        )


def _serialize_product_image(image) -> dict:
    return {
        "id": image.id,
        "url": image.image_path,
        "is_primary": image.is_primary,
    }


@extend_schema_view(
    patch=extend_schema(
        request=UpdateProductImageSerializer,
        responses={200: ProductImageSerializer, 400: DetailErrorSerializer},
    ),
    delete=extend_schema(responses={204: None, 404: DetailErrorSerializer}),
)
class ProductImageDetailView(APIView):
    permission_classes = [IsMerchant]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, store_id: int, product_id: int, image_id: int):
        from features.products.application.use_cases.update_product import (
            UpdateProductImageUseCase,
        )
        from features.products.infrastructure.repositories import DjangoProductRepository
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = UpdateProductImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            image = UpdateProductImageUseCase(
                DjangoProductRepository(),
                DjangoStoreRepository(),
            ).execute(
                UpdateProductImageDTO(
                    product_id=product_id,
                    image_id=image_id,
                    owner_id=request.user.id,
                    is_primary=serializer.validated_data.get("is_primary"),
                    image_file=serializer.validated_data.get("image"),
                )
            )
        except ProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ProductImageNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (StoreNotFoundError, NotStoreOwnerError) as exc:
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(exc, NotStoreOwnerError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response({"detail": str(exc)}, status=status_code)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        product = DjangoProductRepository().get_by_id(product_id)
        if product is None or product.store_id != store_id:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(_serialize_product_image(image))

    def delete(self, request, store_id: int, product_id: int, image_id: int):
        from features.products.application.use_cases.update_product import (
            DeleteProductImageUseCase,
        )
        from features.products.infrastructure.repositories import DjangoProductRepository
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        try:
            DeleteProductImageUseCase(
                DjangoProductRepository(),
                DjangoStoreRepository(),
            ).execute(
                DeleteProductImageDTO(
                    product_id=product_id,
                    image_id=image_id,
                    owner_id=request.user.id,
                )
            )
        except ProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ProductImageNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (StoreNotFoundError, NotStoreOwnerError) as exc:
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(exc, NotStoreOwnerError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response({"detail": str(exc)}, status=status_code)

        product = DjangoProductRepository().get_by_id(product_id)
        if product is None or product.store_id != store_id:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

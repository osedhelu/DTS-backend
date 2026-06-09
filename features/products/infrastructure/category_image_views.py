from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsMerchant
from features.products.application.category_image_serializers import serialize_category_image
from features.products.application.dto import (
    DeleteCategoryImageDTO,
    UpdateCategoryImageDTO,
    UploadCategoryImageDTO,
)
from features.products.domain.exceptions import (
    CategoryImageNotFoundError,
    CategoryNotFoundError,
    DomainValidationError,
)
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.products.infrastructure.category_image_serializers import (
    UpdateCategoryImageSerializer,
    UploadCategoryImageSerializer,
)
from features.products.infrastructure.serializers import ProductImageSerializer


@extend_schema_view(
    get=extend_schema(responses={200: ProductImageSerializer(many=True)}),
    post=extend_schema(
        request=UploadCategoryImageSerializer,
        responses={201: ProductImageSerializer, 400: DetailErrorSerializer},
    ),
)
class CategoryImageUploadView(APIView):
    permission_classes = [IsMerchant]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, store_id: int, category_id: int):
        from features.products.application.category_image_serializers import (
            serialize_category_images,
        )
        from features.products.infrastructure.repositories import DjangoCategoryRepository

        repository = DjangoCategoryRepository()
        category = repository.get_by_id(category_id)
        if category is None or category.store_id != store_id:
            return Response(
                {"detail": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        images, _primary = serialize_category_images(repository.list_images(category_id))
        return Response(images)

    def post(self, request, store_id: int, category_id: int):
        from features.products.application.use_cases.manage_category_image import (
            UploadCategoryImageUseCase,
        )
        from features.products.infrastructure.repositories import DjangoCategoryRepository
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = UploadCategoryImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            image = UploadCategoryImageUseCase(
                DjangoCategoryRepository(),
                DjangoStoreRepository(),
            ).execute(
                UploadCategoryImageDTO(
                    store_id=store_id,
                    category_id=category_id,
                    owner_id=request.user.id,
                    image_file=serializer.validated_data["image"],
                    is_primary=serializer.validated_data.get("is_primary", False),
                )
            )
        except CategoryNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (StoreNotFoundError, NotStoreOwnerError) as exc:
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(exc, NotStoreOwnerError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response({"detail": str(exc)}, status=status_code)

        category = DjangoCategoryRepository().get_by_id(category_id)
        if category is None or category.store_id != store_id:
            return Response(
                {"detail": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(serialize_category_image(image), status=status.HTTP_201_CREATED)


@extend_schema_view(
    patch=extend_schema(
        request=UpdateCategoryImageSerializer,
        responses={200: ProductImageSerializer, 400: DetailErrorSerializer},
    ),
    delete=extend_schema(responses={204: None, 404: DetailErrorSerializer}),
)
class CategoryImageDetailView(APIView):
    permission_classes = [IsMerchant]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, store_id: int, category_id: int, image_id: int):
        from features.products.application.use_cases.manage_category_image import (
            UpdateCategoryImageUseCase,
        )
        from features.products.infrastructure.repositories import DjangoCategoryRepository
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = UpdateCategoryImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            image = UpdateCategoryImageUseCase(
                DjangoCategoryRepository(),
                DjangoStoreRepository(),
            ).execute(
                UpdateCategoryImageDTO(
                    store_id=store_id,
                    category_id=category_id,
                    image_id=image_id,
                    owner_id=request.user.id,
                    is_primary=serializer.validated_data.get("is_primary"),
                    image_file=serializer.validated_data.get("image"),
                )
            )
        except CategoryNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except CategoryImageNotFoundError as exc:
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

        category = DjangoCategoryRepository().get_by_id(category_id)
        if category is None or category.store_id != store_id:
            return Response(
                {"detail": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(serialize_category_image(image))

    def delete(self, request, store_id: int, category_id: int, image_id: int):
        from features.products.application.use_cases.manage_category_image import (
            DeleteCategoryImageUseCase,
        )
        from features.products.infrastructure.repositories import DjangoCategoryRepository
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        try:
            DeleteCategoryImageUseCase(
                DjangoCategoryRepository(),
                DjangoStoreRepository(),
            ).execute(
                DeleteCategoryImageDTO(
                    store_id=store_id,
                    category_id=category_id,
                    image_id=image_id,
                    owner_id=request.user.id,
                )
            )
        except CategoryNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except CategoryImageNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (StoreNotFoundError, NotStoreOwnerError) as exc:
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(exc, NotStoreOwnerError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response({"detail": str(exc)}, status=status_code)

        category = DjangoCategoryRepository().get_by_id(category_id)
        if category is None or category.store_id != store_id:
            return Response(
                {"detail": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

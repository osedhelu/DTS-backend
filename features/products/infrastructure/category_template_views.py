from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsMerchant
from features.products.application.category_templates import (
    CategoryTemplateAlreadyImportedError,
    CategoryTemplateNotFoundError,
)
from features.products.application.use_cases.import_category_template import (
    ImportCategoryTemplateUseCase,
)
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.infrastructure.repositories import DjangoStoreRepository


@extend_schema_view(
    get=extend_schema(
        responses={
            200: inline_serializer(
                name="CategoryTemplateList",
                fields={
                    "vertical": serializers.CharField(),
                    "templates": serializers.ListField(
                        child=inline_serializer(
                            name="CategoryTemplateItem",
                            fields={
                                "name": serializers.CharField(),
                                "subcategories": serializers.ListField(
                                    child=serializers.CharField(),
                                ),
                                "already_imported": serializers.BooleanField(),
                            },
                        ),
                    ),
                },
            )
        }
    )
)
class StoreCategoryTemplateListView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request, store_id: int):
        query = request.query_params.get("q", "")
        use_case = ImportCategoryTemplateUseCase(DjangoStoreRepository())

        try:
            payload = use_case.list_templates(
                store_id=store_id,
                owner_id=request.user.id,
                query=query,
            )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(payload)


class ImportCategoryTemplateSerializer(serializers.Serializer):
    template_name = serializers.CharField(max_length=255)


@extend_schema_view(
    post=extend_schema(
        request=ImportCategoryTemplateSerializer,
        responses={
            201: inline_serializer(
                name="ImportCategoryTemplateResult",
                fields={
                    "template_name": serializers.CharField(),
                    "categories_created": serializers.IntegerField(),
                    "root_category_id": serializers.IntegerField(),
                },
            ),
            400: DetailErrorSerializer,
        },
    )
)
class StoreCategoryTemplateImportView(APIView):
    permission_classes = [IsMerchant]

    def post(self, request, store_id: int):
        serializer = ImportCategoryTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = ImportCategoryTemplateUseCase(DjangoStoreRepository())

        try:
            result = use_case.execute(
                store_id=store_id,
                owner_id=request.user.id,
                template_name=serializer.validated_data["template_name"],
            )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except CategoryTemplateNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except CategoryTemplateAlreadyImportedError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_201_CREATED)

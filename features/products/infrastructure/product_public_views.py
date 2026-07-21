from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.products.domain.entities import ProductDetails
from features.products.infrastructure.repositories import DjangoProductRepository
from features.products.infrastructure.serializers import ProductDetailSerializer


@extend_schema_view(
    get=extend_schema(
        responses={
            200: ProductDetailSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class StoreProductPublicDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, store_id: int, product_id: int):
        from features.products.infrastructure.repositories import DjangoCategoryRepository

        product_repository = DjangoProductRepository()
        product = product_repository.get_by_id(product_id)
        if product is None or product.store_id != store_id or not product.is_active:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        field_config: dict = {}
        category_repository = DjangoCategoryRepository()
        if product.subcategory_id:
            sub = category_repository.get_by_id(product.subcategory_id)
            if sub and sub.field_config:
                field_config = sub.field_config
        elif product.category_id:
            cat = category_repository.get_by_id(product.category_id)
            if cat and cat.field_config:
                field_config = cat.field_config

        details = ProductDetails(
            product=product,
            variants=product_repository.list_variants(product_id),
            ingredients=product_repository.list_ingredients(product_id),
            images=product_repository.list_images(product_id),
        )
        payload = ProductDetailSerializer(details).data
        payload["field_config"] = field_config
        return Response(payload)

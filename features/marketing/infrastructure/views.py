from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from features.accounts.infrastructure.permissions import IsSuperAdmin
from features.marketing.infrastructure.models import BannerModel, CouponModel
from features.marketing.infrastructure.serializers import BannerSerializer, CouponSerializer
from features.products.infrastructure.serializers import ProductSerializer


class CouponViewSet(ModelViewSet):
    queryset = CouponModel.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsSuperAdmin]
    lookup_field = "pk"


class BannerViewSet(ModelViewSet):
    queryset = BannerModel.objects.all().order_by("sort_order", "id")
    serializer_class = BannerSerializer
    permission_classes = [IsSuperAdmin]
    lookup_field = "pk"


@extend_schema_view(
    get=extend_schema(responses={200: BannerSerializer(many=True)}),
)
class ActiveBannersView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        banners = BannerModel.objects.filter(is_active=True).order_by("sort_order", "id")
        return Response(BannerSerializer(banners, many=True).data)


@extend_schema_view(
    get=extend_schema(responses={200: ProductSerializer(many=True)}),
)
class FeaturedProductsView(APIView):
    """Productos destacados para el home del cliente (rail Más vendidos)."""

    permission_classes = [AllowAny]
    LIMIT = 12

    def get(self, request):
        from features.marketing.infrastructure.product_promotion_badges import (
            promotion_badges_for_products,
        )
        from features.products.infrastructure.models import Product
        from features.products.infrastructure.repositories import DjangoProductRepository
        from features.stores.domain.entities import StoreStatus

        products = list(
            Product.objects.filter(
                is_active=True,
                store__is_active=True,
                store__status=StoreStatus.OPEN,
            )
            .select_related("store")
            .order_by("-updated_at")[: self.LIMIT]
        )
        # Si no hay tiendas abiertas, usar activas (mismo fallback que la app).
        if not products:
            products = list(
                Product.objects.filter(
                    is_active=True,
                    store__is_active=True,
                )
                .select_related("store")
                .order_by("-updated_at")[: self.LIMIT]
            )

        if not products:
            return Response([])

        repo = DjangoProductRepository()
        product_ids = [p.id for p in products]
        primary_urls = repo.primary_image_urls_for_products(product_ids)

        promotion_badges: dict[int, str | None] = {}
        by_store: dict[int, list[int]] = {}
        for p in products:
            by_store.setdefault(p.store_id, []).append(p.id)
        for store_id, ids in by_store.items():
            promotion_badges.update(promotion_badges_for_products(store_id, ids))

        payload = ProductSerializer(
            products,
            many=True,
            context={
                "primary_image_urls": primary_urls,
                "promotion_badges": promotion_badges,
            },
        ).data

        # Enriquecer con store_name (lo espera flutter-customer FeaturedProduct).
        store_names = {p.id: p.store.name for p in products}
        for item in payload:
            item["store_name"] = store_names.get(item["id"], "Comercio")

        return Response(payload)

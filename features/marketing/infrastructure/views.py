from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from features.accounts.infrastructure.permissions import IsSuperAdmin
from features.marketing.infrastructure.models import BannerModel, CouponModel
from features.marketing.infrastructure.serializers import BannerSerializer, CouponSerializer


class CouponViewSet(ModelViewSet):
    queryset = CouponModel.objects.all()
    serializer_class = CouponSerializer
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

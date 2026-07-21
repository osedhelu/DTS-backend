from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework.views import APIView

from features.accounts.application.use_cases.get_admin_operations_map import (
    GetAdminOperationsMapUseCase,
)
from features.accounts.infrastructure.admin_map_views import (
    AdminOperationsMapSerializer,
    _serialize_map,
)
from features.accounts.infrastructure.permissions import IsMerchant


@extend_schema_view(
    get=extend_schema(responses={200: AdminOperationsMapSerializer}),
)
class MerchantOperationsMapView(APIView):
    """Mapa operativo del comercio: sus tiendas y entregas activas con GPS del conductor."""

    permission_classes = [IsMerchant]

    def get(self, request):
        data = GetAdminOperationsMapUseCase().execute(owner_id=request.user.id)
        return Response(_serialize_map(data))

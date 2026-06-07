from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsSuperAdmin
from features.stores.application.use_cases.update_store_moderation import (
    UpdateStoreModerationUseCase,
)
from features.stores.domain.exceptions import StoreNotFoundError
from features.stores.infrastructure.repositories import DjangoStoreRepository
from features.stores.infrastructure.serializers import StoreSerializer


class StoreModerationSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()


@extend_schema_view(
    patch=extend_schema(
        request=StoreModerationSerializer,
        responses={200: StoreSerializer, 404: DetailErrorSerializer},
    ),
)
class AdminStoreModerationView(APIView):
    permission_classes = [IsSuperAdmin]

    def patch(self, request, store_id: int):
        serializer = StoreModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = UpdateStoreModerationUseCase(DjangoStoreRepository())
        try:
            store = use_case.execute(store_id, serializer.validated_data["is_active"])
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(StoreSerializer(store).data)

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsMerchant
from features.stores.application.dto import CreateStoreDTO, UpdateStoreStatusDTO
from features.stores.domain.entities import StoreStatus
from features.stores.domain.exceptions import (
    DomainValidationError,
    NotStoreOwnerError,
    StoreNotFoundError,
)
from features.stores.infrastructure.serializers import (
    CreateStoreSerializer,
    StoreSerializer,
    UpdateStoreStatusSerializer,
)


@extend_schema_view(
    get=extend_schema(responses={200: StoreSerializer(many=True)}),
    post=extend_schema(
        request=CreateStoreSerializer,
        responses={201: StoreSerializer, 400: DetailErrorSerializer},
    ),
)
class StoreListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMerchant()]
        return [AllowAny()]

    def get(self, request):
        from features.stores.infrastructure.repositories import DjangoStoreRepository
        from features.stores.infrastructure.serializers import StoreSerializer

        repository = DjangoStoreRepository()
        stores = repository.list_all()
        serializer = StoreSerializer(stores, many=True)
        return Response(serializer.data)

    def post(self, request):
        from features.stores.application.use_cases.create_store import CreateStoreUseCase
        from features.stores.infrastructure.repositories import DjangoStoreRepository
        from features.stores.infrastructure.serializers import CreateStoreSerializer, StoreSerializer

        serializer = CreateStoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = CreateStoreUseCase(DjangoStoreRepository())
        try:
            store = use_case.execute(
                CreateStoreDTO(
                    owner_id=request.user.id,
                    name=data["name"],
                    latitude=data["latitude"],
                    longitude=data["longitude"],
                    address=data.get("address", ""),
                    status=StoreStatus(data.get("status", StoreStatus.CLOSED)),
                )
            )
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StoreSerializer(store).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    patch=extend_schema(
        request=UpdateStoreStatusSerializer,
        responses={
            200: StoreSerializer,
            400: DetailErrorSerializer,
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class StoreDetailView(APIView):
    permission_classes = [IsMerchant]

    def patch(self, request, store_id: int):
        from features.stores.application.use_cases.update_store_status import (
            UpdateStoreStatusUseCase,
        )
        from features.stores.infrastructure.repositories import DjangoStoreRepository
        from features.stores.infrastructure.serializers import (
            StoreSerializer,
            UpdateStoreStatusSerializer,
        )

        serializer = UpdateStoreStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = UpdateStoreStatusUseCase(DjangoStoreRepository())
        try:
            store = use_case.execute(
                UpdateStoreStatusDTO(
                    store_id=store_id,
                    owner_id=request.user.id,
                    status=StoreStatus(serializer.validated_data["status"]),
                )
            )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StoreSerializer(store).data)

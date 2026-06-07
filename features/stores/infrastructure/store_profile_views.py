from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsMerchant
from features.stores.application.dto import UpdateStoreProfileDTO
from features.stores.application.use_cases.update_store_profile import (
    UpdateStoreProfileUseCase,
)
from features.stores.domain.entities import StoreStatus
from features.stores.domain.exceptions import (
    DomainValidationError,
    NotStoreOwnerError,
    StoreNotFoundError,
)
from features.stores.infrastructure.serializers import (
    StoreSerializer,
    UpdateStoreProfileSerializer,
)


@extend_schema_view(
    get=extend_schema(
        responses={
            200: StoreSerializer,
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
    patch=extend_schema(
        request=UpdateStoreProfileSerializer,
        responses={
            200: StoreSerializer,
            400: DetailErrorSerializer,
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class StoreProfileView(APIView):
    permission_classes = [IsMerchant]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, store_id: int):
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        use_case = UpdateStoreProfileUseCase(DjangoStoreRepository())
        try:
            store = use_case.get_profile(store_id, request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(StoreSerializer(store).data)

    def patch(self, request, store_id: int):
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = UpdateStoreProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = UpdateStoreProfileUseCase(DjangoStoreRepository())
        try:
            store = use_case.execute(
                UpdateStoreProfileDTO(
                    store_id=store_id,
                    owner_id=request.user.id,
                    name=data.get("name"),
                    description=data.get("description"),
                    phone=data.get("phone"),
                    address=data.get("address"),
                    status=StoreStatus(data["status"]) if "status" in data else None,
                    logo_file=data.get("logo"),
                )
            )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StoreSerializer(store).data)

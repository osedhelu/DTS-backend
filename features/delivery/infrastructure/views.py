from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsCustomer, IsDriver
from features.delivery.domain.exceptions import (
    DomainValidationError,
    InvalidOrderStatusForTrackingError,
    ServiceOrderNotTrackableError,
    UnauthorizedDriverError,
    UnauthorizedTrackingAccessError,
)
from features.orders.domain.exceptions import OrderNotFoundError
from features.delivery.infrastructure.serializers import (
    DeliveryTrackingSerializer,
    RecordLocationSerializer,
)


@extend_schema_view(
    get=extend_schema(
        responses={
            200: DeliveryTrackingSerializer,
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
    post=extend_schema(
        request=RecordLocationSerializer,
        responses={
            201: DeliveryTrackingSerializer,
            400: DetailErrorSerializer,
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class OrderTrackingView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsDriver()]
        return [IsCustomer()]

    def get(self, request, order_id: int):
        from features.delivery.application.use_cases.get_order_tracking import (
            GetOrderTrackingUseCase,
        )
        from features.delivery.infrastructure.repositories import DjangoDeliveryTrackingRepository
        from features.delivery.infrastructure.serializers import DeliveryTrackingSerializer
        from features.orders.infrastructure.repositories import DjangoOrderRepository

        use_case = GetOrderTrackingUseCase(
            DjangoOrderRepository(),
            DjangoDeliveryTrackingRepository(),
        )

        try:
            tracking = use_case.execute(order_id=order_id, customer_id=request.user.id)
        except OrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except UnauthorizedTrackingAccessError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(DeliveryTrackingSerializer(tracking).data)

    def post(self, request, order_id: int):
        from features.delivery.application.dto import RecordLocationDTO
        from features.delivery.application.use_cases.record_location import RecordLocationUseCase
        from features.delivery.infrastructure.repositories import DjangoDeliveryTrackingRepository
        from features.delivery.infrastructure.serializers import (
            DeliveryTrackingSerializer,
            RecordLocationSerializer,
        )
        from features.orders.infrastructure.repositories import DjangoOrderRepository

        serializer = RecordLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = RecordLocationUseCase(
            DjangoOrderRepository(),
            DjangoDeliveryTrackingRepository(),
        )

        try:
            tracking = use_case.execute(
                RecordLocationDTO(
                    order_id=order_id,
                    driver_id=request.user.id,
                    latitude=data["latitude"],
                    longitude=data["longitude"],
                    recorded_at=data.get("recorded_at") or timezone.now(),
                )
            )
        except OrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except UnauthorizedDriverError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except (
            InvalidOrderStatusForTrackingError,
            ServiceOrderNotTrackableError,
            DomainValidationError,
        ) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            DeliveryTrackingSerializer(tracking).data,
            status=status.HTTP_201_CREATED,
        )

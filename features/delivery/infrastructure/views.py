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
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        use_case = GetOrderTrackingUseCase(
            DjangoOrderRepository(),
            DjangoDeliveryTrackingRepository(),
            DjangoStoreRepository(),
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


@extend_schema_view(
    get=extend_schema(
        responses={200: "DriverOfferSerializer"},
    ),
)
class DriverOffersListView(APIView):
    permission_classes = [IsDriver]

    def get(self, request):
        from features.delivery.application.use_cases.list_driver_offers import (
            ListDriverOffersUseCase,
        )
        from features.delivery.domain.exceptions import DriverProfileNotFoundForOffersError
        from features.delivery.infrastructure.serializers import DriverOfferSerializer

        try:
            offers = ListDriverOffersUseCase().execute(request.user.id)
        except DriverProfileNotFoundForOffersError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        payload = [
            {
                "order_id": o.order_id,
                "store_id": o.store_id,
                "store_name": o.store_name,
                "store_latitude": o.store_latitude,
                "store_longitude": o.store_longitude,
                "total": o.total,
                "distance_km": o.distance_km,
                "status": o.status,
            }
            for o in offers
        ]
        return Response(DriverOfferSerializer(payload, many=True).data)


class AcceptOfferView(APIView):
    permission_classes = [IsDriver]

    def post(self, request, order_id: int):
        from features.delivery.application.use_cases.accept_offer import AcceptOfferUseCase
        from features.delivery.domain.exceptions import (
            OfferAlreadyTakenError,
            OfferNotAcceptableError,
        )
        from features.delivery.infrastructure.serializers import AcceptOfferResponseSerializer
        from features.orders.domain.value_objects import OrderStatus

        try:
            driver_id = AcceptOfferUseCase().execute(order_id, request.user.id)
        except OrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except OfferAlreadyTakenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        except OfferNotAcceptableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            AcceptOfferResponseSerializer(
                {
                    "order_id": order_id,
                    "driver_id": driver_id,
                    "status": OrderStatus.DRIVER_ASSIGNED,
                }
            ).data,
            status=status.HTTP_200_OK,
        )


class RejectOfferView(APIView):
    permission_classes = [IsDriver]

    def post(self, request, order_id: int):
        from features.delivery.application.use_cases.reject_offer import RejectOfferUseCase

        RejectOfferUseCase().execute(order_id, request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)

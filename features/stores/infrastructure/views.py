from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.pagination import paginate_list
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
        from features.accounts.infrastructure.models import CustomerProfile
        from features.delivery.domain.constants import normalize_radius_km
        from features.delivery.domain.services import DriverMatcher
        from features.stores.domain.value_objects import GeoLocation
        from features.stores.infrastructure.repositories import DjangoStoreRepository
        from features.stores.infrastructure.serializers import StoreSerializer

        status_filter = request.query_params.get("status")
        parsed_status = StoreStatus(status_filter) if status_filter else None

        repository = DjangoStoreRepository()
        stores = repository.list_all(status=parsed_status)

        center: GeoLocation | None = None
        radius_km: float | None = None

        lat_raw = request.query_params.get("latitude")
        lng_raw = request.query_params.get("longitude")
        radius_raw = request.query_params.get("radius_km")

        if lat_raw is not None or lng_raw is not None or radius_raw is not None:
            if lat_raw is None or lng_raw is None:
                return Response(
                    {"detail": "Debes enviar latitude y longitude juntos"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                center = GeoLocation(
                    latitude=float(lat_raw),
                    longitude=float(lng_raw),
                )
                radius_km = normalize_radius_km(
                    radius_raw if radius_raw is not None else None
                )
            except (TypeError, ValueError) as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif request.user.is_authenticated and getattr(
            request.user, "is_customer", False
        ):
            try:
                profile = CustomerProfile.objects.get(user_id=request.user.id)
            except CustomerProfile.DoesNotExist:
                profile = None
            if profile is not None and profile.has_search_center:
                center = GeoLocation(
                    latitude=profile.search_center_latitude,
                    longitude=profile.search_center_longitude,
                )
                radius_km = float(profile.search_radius_km)

        if center is not None and radius_km is not None:
            stores = [
                store
                for store in stores
                if DriverMatcher.covers_point(
                    point=GeoLocation(
                        latitude=store.latitude,
                        longitude=store.longitude,
                    ),
                    center=center,
                    radius_km=radius_km,
                )
            ]

        return paginate_list(
            request,
            stores,
            lambda page: StoreSerializer(page, many=True).data,
        )

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


@extend_schema_view(
    get=extend_schema(
        responses={
            200: inline_serializer(
                name="MerchantDashboard",
                fields={
                    "store_id": serializers.IntegerField(),
                    "period_days": serializers.IntegerField(),
                    "total_sales": serializers.DecimalField(max_digits=14, decimal_places=2),
                    "order_count": serializers.IntegerField(),
                    "orders_today": serializers.IntegerField(),
                    "orders_this_week": serializers.IntegerField(),
                    "paid_today_count": serializers.IntegerField(),
                    "paid_today_total": serializers.DecimalField(
                        max_digits=14,
                        decimal_places=2,
                    ),
                    "average_ticket": serializers.DecimalField(max_digits=14, decimal_places=2),
                    "platform_commission_rate": serializers.DecimalField(
                        max_digits=5,
                        decimal_places=4,
                    ),
                    "platform_commission": serializers.DecimalField(
                        max_digits=14,
                        decimal_places=2,
                    ),
                    "net_earnings": serializers.DecimalField(max_digits=14, decimal_places=2),
                    "active_products": serializers.IntegerField(),
                    "sales_series": serializers.ListField(child=serializers.DictField()),
                    "top_products": serializers.ListField(child=serializers.DictField()),
                },
            ),
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class MerchantDashboardView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request, store_id: int):
        from features.stores.application.use_cases.get_merchant_dashboard import (
            GetMerchantDashboardUseCase,
        )
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        days = int(request.query_params.get("days", 30))

        try:
            payload = GetMerchantDashboardUseCase(DjangoStoreRepository()).execute(
                store_id=store_id,
                owner_id=request.user.id,
                days=days,
            )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(payload)


@extend_schema_view(
    get=extend_schema(responses={200: StoreSerializer(many=True)}),
)
class MerchantStoreListView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request):
        from features.stores.infrastructure.repositories import DjangoStoreRepository
        from features.stores.infrastructure.serializers import StoreSerializer

        repository = DjangoStoreRepository()
        stores = repository.list_by_owner(request.user.id, active_only=False)
        return paginate_list(
            request,
            stores,
            lambda page: StoreSerializer(page, many=True).data,
        )

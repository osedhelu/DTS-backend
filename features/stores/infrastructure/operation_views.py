"""Vistas de horarios, zonas y detalle público de tienda."""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsMerchant
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.domain.services import DeliveryZoneService, OpeningHoursService
from features.stores.domain.value_objects import GeoLocation
from features.stores.infrastructure.models import DeliveryZone, Store, StoreOpeningHours
from features.stores.infrastructure.operation_serializers import (
    CreateDeliveryZoneSerializer,
    DeliveryCoverageQuerySerializer,
    DeliveryZoneSerializer,
    OpeningHoursBulkSerializer,
    StorePublicDetailSerializer,
    UpdateDeliveryZoneSerializer,
)
from features.stores.infrastructure.repositories import DjangoStoreRepository
from features.stores.infrastructure.serializers import StoreSerializer


def _assert_store_owner(store_id: int, owner_id: int) -> Store:
    store = Store.objects.filter(pk=store_id).first()
    if store is None:
        raise StoreNotFoundError(f"Comercio {store_id} no encontrado")
    if store.owner_id != owner_id:
        raise NotStoreOwnerError("No eres dueño de este comercio")
    return store


def _serialize_opening_hours(store_id: int) -> list[dict]:
    return [
        {
            "day_of_week": row.day_of_week,
            "open_time": row.open_time,
            "close_time": row.close_time,
            "is_closed": row.is_closed,
        }
        for row in StoreOpeningHours.objects.filter(store_id=store_id).order_by(
            "day_of_week"
        )
    ]


def _serialize_delivery_zones(store_id: int) -> list[dict]:
    return DeliveryZoneSerializer(
        DeliveryZone.objects.filter(store_id=store_id).order_by("name"),
        many=True,
    ).data


def build_public_store_detail(
    store_id: int,
    *,
    customer_lat: float | None = None,
    customer_lng: float | None = None,
) -> dict:
    from core.media_urls import build_public_media_url

    store = Store.objects.filter(pk=store_id, is_active=True).first()
    if store is None:
        raise StoreNotFoundError(f"Comercio {store_id} no encontrado")

    hours_rows = list(
        StoreOpeningHours.objects.filter(store_id=store_id).order_by("day_of_week")
    )
    from features.stores.domain.services import OpeningHoursSlot

    slots = [
        OpeningHoursSlot(
            day_of_week=row.day_of_week,
            open_time=row.open_time,
            close_time=row.close_time,
            is_closed=row.is_closed,
        )
        for row in hours_rows
    ]
    schedule_open = OpeningHoursService.is_open_now(slots) if store.use_schedule else True

    zones = list(
        DeliveryZone.objects.filter(store_id=store_id).values_list(
            "center_latitude",
            "center_longitude",
            "radius_km",
            "is_active",
        )
    )
    in_zone = True
    if customer_lat is not None and customer_lng is not None:
        in_zone = DeliveryZoneService.is_within_any_zone(
            zones,
            GeoLocation(latitude=customer_lat, longitude=customer_lng),
        )

    is_open = store.status == "open" and schedule_open
    accepts = is_open and in_zone

    payload = {
        "id": store.id,
        "name": store.name,
        "status": store.status,
        "vertical": store.vertical,
        "latitude": store.latitude,
        "longitude": store.longitude,
        "address": store.address,
        "description": store.description,
        "phone": store.phone,
        "logo_url": build_public_media_url(store.logo.url if store.logo else ""),
        "is_open": is_open,
        "use_schedule": store.use_schedule,
        "opening_hours": _serialize_opening_hours(store_id),
        "delivery_zones": _serialize_delivery_zones(store_id),
        "accepts_orders": accepts,
    }
    if customer_lat is not None and customer_lng is not None:
        payload["in_delivery_zone"] = in_zone
    return payload


@extend_schema_view(
    get=extend_schema(
        responses={200: StorePublicDetailSerializer, 404: DetailErrorSerializer},
    ),
)
class StorePublicDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, store_id: int):
        lat = request.query_params.get("latitude")
        lng = request.query_params.get("longitude")
        try:
            payload = build_public_store_detail(
                store_id,
                customer_lat=float(lat) if lat else None,
                customer_lng=float(lng) if lng else None,
            )
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(payload)


@extend_schema_view(
    get=extend_schema(responses={200: OpeningHoursBulkSerializer}),
    put=extend_schema(
        request=OpeningHoursBulkSerializer,
        responses={200: OpeningHoursBulkSerializer, 403: DetailErrorSerializer},
    ),
)
class StoreOpeningHoursView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request, store_id: int):
        try:
            store = _assert_store_owner(store_id, request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(
            {
                "use_schedule": store.use_schedule,
                "slots": _serialize_opening_hours(store_id),
            }
        )

    def put(self, request, store_id: int):
        serializer = OpeningHoursBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            store = _assert_store_owner(store_id, request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        if "use_schedule" in data:
            store.use_schedule = data["use_schedule"]
            store.save(update_fields=["use_schedule", "updated_at"])

        StoreOpeningHours.objects.filter(store_id=store_id).delete()
        for slot in data["slots"]:
            StoreOpeningHours.objects.create(
                store_id=store_id,
                day_of_week=slot["day_of_week"],
                open_time=slot.get("open_time"),
                close_time=slot.get("close_time"),
                is_closed=slot.get("is_closed", False),
            )

        return Response(
            {
                "use_schedule": store.use_schedule,
                "slots": _serialize_opening_hours(store_id),
            }
        )


@extend_schema_view(
    get=extend_schema(responses={200: DeliveryZoneSerializer(many=True)}),
    post=extend_schema(
        request=CreateDeliveryZoneSerializer,
        responses={201: DeliveryZoneSerializer},
    ),
)
class StoreDeliveryZoneListView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request, store_id: int):
        try:
            _assert_store_owner(store_id, request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        zones = DeliveryZone.objects.filter(store_id=store_id).order_by("name")
        return Response(DeliveryZoneSerializer(zones, many=True).data)

    def post(self, request, store_id: int):
        serializer = CreateDeliveryZoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            _assert_store_owner(store_id, request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        zone = DeliveryZone.objects.create(store_id=store_id, **data)
        return Response(DeliveryZoneSerializer(zone).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    patch=extend_schema(
        request=UpdateDeliveryZoneSerializer,
        responses={200: DeliveryZoneSerializer, 404: DetailErrorSerializer},
    ),
    delete=extend_schema(responses={204: None, 404: DetailErrorSerializer}),
)
class StoreDeliveryZoneDetailView(APIView):
    permission_classes = [IsMerchant]

    def patch(self, request, store_id: int, zone_id: int):
        serializer = UpdateDeliveryZoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            _assert_store_owner(store_id, request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        zone = DeliveryZone.objects.filter(pk=zone_id, store_id=store_id).first()
        if zone is None:
            return Response({"detail": "Zona no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        for key, value in serializer.validated_data.items():
            setattr(zone, key, value)
        zone.save()
        return Response(DeliveryZoneSerializer(zone).data)

    def delete(self, request, store_id: int, zone_id: int):
        try:
            _assert_store_owner(store_id, request.user.id)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        deleted, _ = DeliveryZone.objects.filter(pk=zone_id, store_id=store_id).delete()
        if not deleted:
            return Response({"detail": "Zona no encontrada"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        parameters=[DeliveryCoverageQuerySerializer],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "in_delivery_zone": {"type": "boolean"},
                    "accepts_orders": {"type": "boolean"},
                    "is_open": {"type": "boolean"},
                },
            },
            404: DetailErrorSerializer,
        },
    ),
)
class StoreCoverageCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, store_id: int):
        serializer = DeliveryCoverageQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        lat = serializer.validated_data["latitude"]
        lng = serializer.validated_data["longitude"]

        try:
            detail = build_public_store_detail(store_id, customer_lat=lat, customer_lng=lng)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "in_delivery_zone": detail["in_delivery_zone"],
                "accepts_orders": detail["accepts_orders"],
                "is_open": detail["is_open"],
            }
        )

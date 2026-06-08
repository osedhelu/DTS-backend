from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from features.accounts.application.use_cases.get_admin_operations_map import (
    AdminMapDeliveryRow,
    AdminMapStoreRow,
    AdminOperationsMapData,
    GetAdminOperationsMapUseCase,
)
from features.accounts.infrastructure.permissions import IsSuperAdmin


class AdminMapStoreSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    is_active = serializers.BooleanField()
    vertical = serializers.CharField()
    address = serializers.CharField()


class AdminMapDeliverySerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    status = serializers.CharField()
    order_type = serializers.CharField()
    store_id = serializers.IntegerField()
    store_name = serializers.CharField()
    store_latitude = serializers.FloatField()
    store_longitude = serializers.FloatField()
    driver_id = serializers.IntegerField(allow_null=True)
    destination_latitude = serializers.FloatField(allow_null=True)
    destination_longitude = serializers.FloatField(allow_null=True)
    destination_label = serializers.CharField()
    latest_latitude = serializers.FloatField(allow_null=True)
    latest_longitude = serializers.FloatField(allow_null=True)
    latest_recorded_at = serializers.DateTimeField(allow_null=True)


class AdminOperationsMapSerializer(serializers.Serializer):
    stores = AdminMapStoreSerializer(many=True)
    active_deliveries = AdminMapDeliverySerializer(many=True)


def _serialize_store(row: AdminMapStoreRow) -> dict:
    return AdminMapStoreSerializer(
        {
            "id": row.id,
            "name": row.name,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "is_active": row.is_active,
            "vertical": row.vertical,
            "address": row.address,
        }
    ).data


def _serialize_delivery(row: AdminMapDeliveryRow) -> dict:
    return AdminMapDeliverySerializer(
        {
            "order_id": row.order_id,
            "status": row.status,
            "order_type": row.order_type,
            "store_id": row.store_id,
            "store_name": row.store_name,
            "store_latitude": row.store_latitude,
            "store_longitude": row.store_longitude,
            "driver_id": row.driver_id,
            "destination_latitude": row.destination_latitude,
            "destination_longitude": row.destination_longitude,
            "destination_label": row.destination_label,
            "latest_latitude": row.latest_latitude,
            "latest_longitude": row.latest_longitude,
            "latest_recorded_at": row.latest_recorded_at,
        }
    ).data


def _serialize_map(data: AdminOperationsMapData) -> dict:
    return AdminOperationsMapSerializer(
        {
            "stores": [_serialize_store(store) for store in data.stores],
            "active_deliveries": [
                _serialize_delivery(delivery) for delivery in data.active_deliveries
            ],
        }
    ).data


@extend_schema_view(
    get=extend_schema(responses={200: AdminOperationsMapSerializer}),
)
class AdminOperationsMapView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        data = GetAdminOperationsMapUseCase().execute()
        return Response(_serialize_map(data))
